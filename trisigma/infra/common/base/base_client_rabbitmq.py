import asyncio
from bunny_storm import AsyncAdapter, RabbitMQConnectionData
import uuid
import json
import logging

class BaseClientRabbitMQ:

    _rpc_adapter = None
    _stream_adapter = None
    _callbacks = {}
    _rpc_queue = None
    _stream_recv_queue = None
    _logger = None
    _pending_subs = []
    _connected = False

    def __init__(self, target, logger=None, loop=None, **conn_params):
        self.target = target
        self._rpc_queue = uuid.uuid4().hex
        self._rpc_exchange = f"{target}-rpc"
        self._stream_queue = uuid.uuid4().hex
        self._stream_exchange = f"{target}-stream"
        self._logger = logger or logging.getLogger(__name__)
        assert isinstance(self._logger, logging.Logger)
        self._loop = loop or asyncio.get_event_loop()
        self._conn_params = conn_params

    async def connect(self):
        self._connection = RabbitMQConnectionData(**self._conn_params)
        self._rpc_adapter = self._prepare_rpc_adapter()
        self._stream_adapter = self._prepare_stream_adapter()
        self._loop.create_task(
            self._stream_adapter.receive(self._handle, self._stream_queue))
        self._connected = True

    def _prepare_rpc_adapter(self):
        assert self._logger
        conf = dict(
            publish=dict(
                publisher=dict(
                    exchange_name=self._rpc_exchange,
                    exchange_type="direct",
                    routing_key="host"),
            ),
            receive=dict(
                receiver=dict(
                    exchange_name=self._rpc_exchange,
                    exchange_type="direct",
                    queue_name=self._rpc_queue,
                )
            ),
        )
        adapter = AsyncAdapter(
            rabbitmq_connection_data=self._connection,
            configuration=conf,
            loop=self._loop,
            logger=self._logger)
        return adapter

    def _prepare_stream_adapter(self):
        assert self._logger
        conf = dict(
            receive=dict(
                reciver=dict(
                    exchange_name=self._stream_exchange,
                    exchange_type="fanout",
                    queue_name=self._stream_queue,
                    routing_key="null",
                )
            )
        )
        adapter = AsyncAdapter(
            rabbitmq_connection_data=self._connection,
            configuration=conf,
            loop=self._loop,
            logger=self._logger)
        return adapter

    def subscribe(self, event_name, callback):
        assert self._connected, "Not connected"
        assert self._stream_adapter, "Not connected"
        self._callbacks[event_name] = callback
        conf = dict(
            exchange_name=self._stream_exchange,
            exchange_type="fanout",
            queue_name=self._stream_queue,
            routing_key=event_name,
        )
        self._stream_adapter.add_consumer(conf)

    async def request(self, endpoint, params={}):
        assert self._logger
        assert self._rpc_adapter
        assert self._rpc_queue
        req = dict(endpoint=endpoint, params=params)
        try:
            payload = json.dumps(req).encode()
        except Exception as e:
            self._logger.error("Error encoding request: %s" % e, exc_info=True)
            raise
        resp = await self._rpc_adapter.rpc(
            body=payload,
            receive_queue=self._rpc_queue,
            publish_exchange=self._rpc_exchange,
            ttl=100,
            timeout=10)
        try:
            data = json.loads(resp.decode())
        except Exception as e:
            self._logger.error("Error decoding response: %s" % e, exc_info=True)
            raise
        assert data["status"] == "ok", data['message']
        return data["message"]

    async def _handle(self, logger, message):
        body = message.body.decode()
        try:
            event = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON Request: %s" % body, exc_info=True)
            return
        assert "event_name" in event
        assert "data" in event
        await self._handle_event(logger, event)

    async def _handle_event(self, logger, event):
        fn = self._callbacks.get(event["event_name"])
        if fn:
            try:
                await fn(event["data"])
            except Exception:
                logger.error(
                    "Error handling event: %s" % event['event_name'],
                    exc_info=True)


