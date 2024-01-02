import asyncio
from bunny_storm import AsyncAdapter, RabbitMQConnectionData
import logging
import json
import uuid

class BaseServerRabbitMQ:

    _connection = None
    _callbacks = {}
    _rpc_adapter = None
    _stream_adapter = None

    def __init__(self, server_name, prefetch_count=1, logger=None, loop=None, **conn_params):
        self._rpc_exchange = f"{server_name}-rpc"
        self._stream_exchange = f"{server_name}-stream"
        self._queue_name = uuid.uuid4().hex
        self._prefetch_count = prefetch_count
        self._logger = logger or logging.getLogger(__name__)
        self._conn_params = conn_params
        self._loop = loop or asyncio.get_event_loop()

    def register(self, name):
        def decorator(fn):
            self._callbacks[name] = fn
            return fn
        return decorator

    async def publish(self, topic, message):
        try:
            data = {"event_name": topic, "data": message}
            payload = json.dumps(data).encode()
        except Exception:
            self._logger.error("Invalid JSON message: %s" % str(message), exc_info=True)
            return
        try:
            assert self._stream_adapter is not None, "Stream adapter not set"
            await self._stream_adapter.publish(
                body=payload,
                exchange=self._stream_exchange,
                routing_key=topic)
        except Exception:
            self._logger.error("Error publishing message: %s" % str(message), exc_info=True)

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
        self._connection = RabbitMQConnectionData(**self._conn_params)
        self._rpc_adapter = self._prepare_rpc_adapter()
        self._stream_adapter = self._prepare_stream_adapter()
        self._loop.create_task(self._rpc_adapter.receive(self._handle, self._queue_name))

    def _prepare_rpc_adapter(self):
        assert self._connection is not None, "Connection not set"
        conf = dict(
            publish=dict(
                publisher=dict(
                    exchange_name=self._rpc_exchange,
                    exchange_type="direct",
                    routing_key="host"),
            ),
            receive=dict(
                consumer=dict(
                    exchange_name=self._rpc_exchange,
                    exchange_type="direct",
                    routing_key="host",
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

    def _prepare_stream_adapter(self):
        assert self._connection is not None, "Connection not set"
        conf = dict(
            publish=dict(
                publisher=dict(
                    exchange_name=self._stream_exchange,
                    exchange_type="fanout",
                    routing_key="host"),
            ),
        )
        adapter = AsyncAdapter(
            rabbitmq_connection_data=self._connection,
            configuration=conf,
            loop=self._loop,
            logger=self._logger)
        return adapter


