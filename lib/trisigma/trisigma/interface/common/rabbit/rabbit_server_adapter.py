import time
import asyncio
from bunny_storm import AsyncAdapter, RabbitMQConnectionData
import logging
import json
import uuid

class RabbitServerAdapter:

    _uri = None
    _connection = None
    _callbacks = {}
    _rpc_adapter = None

    def __init__(self, uri, exchange, server_name, prefetch_count=1, queue_name=None, logger=None, loop=None):
        self._connection = self._prepare_connection(uri)
        self._exchange = exchange + "-rpc"
        self._server_name = server_name
        self._queue_name = queue_name or uuid.uuid4().hex
        self._prefetch_count = prefetch_count
        self._logger = logger or logging.getLogger(__name__)
        self._loop = loop or asyncio.get_event_loop()

    def _prepare_connection(self, uri):
        assert uri.startswith("amqp://")
        usr, pwd = uri.split("@")[0][len("amqp://"):].split(":")
        host, port = uri.split("@")[1].split("/")[0].split(":")
        vhost = uri.split("/")[-1]
        connection = RabbitMQConnectionData(
            host=host, port=port,
            username=usr, password=pwd, virtual_host=vhost)
        return connection

    def register(self, name, fn):
        self._callbacks[name] = fn

    async def _handle_request(self, logger, req):
        if "endpoint" not in req or "params" not in req:
            logger.error("Invalid request: %s", str(req))
            return {"status": "error", "message": "Invalid request"}
        fn = self._callbacks.get(req["endpoint"], None)
        if fn is None:
            logger.error("Unknown request: %s", req["endpoint"])
            return {"status": "error", "message": "Unknown request"}
        try:
            body = await fn(**req["params"])
            return {"status": "ok", "message": body}
        except Exception as e:
            logger.error("Exception in request handler", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _handle(self, logger, message):
        body = message.body.decode()
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON Request: %s" % body, exc_info=True)
            resp = {"status": "error", "message": "Invalid JSON"}
            return json.dumps(resp).encode()
        resp = await self._handle_request(logger, req)
        try:
            return json.dumps(resp).encode()
        except json.JSONDecodeError:
            logger.error("Invalid JSON Response: %s" % str(resp), exc_info=True)
            return json.dumps({"status": "error", "message": "Invalid JSON"}).encode()

    async def start(self):
        self._rpc_adapter = self._prepare_rpc_adapter()
        self._loop.create_task(self._rpc_adapter.receive(self._handle, self._queue_name))

    def _prepare_rpc_adapter(self):
        assert self._connection is not None, "Connection not set"
        conf = dict(
            publish=dict(
                publisher=dict(
                    exchange_name=self._exchange,
                    exchange_type="direct",
                    routing_key=self._server_name),
            ),
            receive=dict(
                consumer=dict(
                    exchange_name=self._exchange,
                    exchange_type="direct",
                    routing_key=self._server_name,
                    queue_name=self._queue_name,
                    prefetch_count=self._prefetch_count,
                )
            )
        )
        adapter = AsyncAdapter(
            rabbitmq_connection_data=self._connection,
            configuration=conf,
            loop=self._loop,
            logger=self._logger)
        return adapter
