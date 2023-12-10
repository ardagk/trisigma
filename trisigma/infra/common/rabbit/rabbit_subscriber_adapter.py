import asyncio
from bunny_storm import AsyncAdapter, RabbitMQConnectionData
import uuid
import json
import logging

class RabbitSubscriberAdapter:

    _stream_adapter = None
    _connected = False

    def __init__(self, uri, exchange, prefetch_count=1, queue_name=None, logger=None, loop=None):
        self._callbacks = {}
        self._pending_subscriptions = []
        self._connection = self._prepare_connection(uri)
        self._queue = queue_name or uuid.uuid4().hex
        self._exchange = f"{exchange}-pubsub"
        self._logger = logger or logging.getLogger(__name__)
        assert isinstance(self._logger, logging.Logger)
        self._loop = loop or asyncio.get_event_loop()
        self._adapters = {}

    def _prepare_connection(self, uri):
        assert uri.startswith("amqp://")
        usr, pwd = uri.split("@")[0][len("amqp://"):].split(":")
        host, port = uri.split("@")[1].split("/")[0].split(":")
        vhost = uri.split("/")[-1]
        connection = RabbitMQConnectionData(
            host=host, port=port,
            username=usr, password=pwd, virtual_host=vhost)
        return connection

    async def connect(self):
        self._stream_adapter = self._prepare_stream_adapter()
        self._loop.create_task(
            self._stream_adapter.receive(self._handle, self._queue))
        self._connected = True
        for topic, callback in self._pending_subscriptions:
            self._subscribe(topic, callback)

    def _prepare_stream_adapter(self, routing_key='null'):
        if routing_key not in self._adapters:
            conf = dict(
                receive=dict(
                    reciver=dict(
                        exchange_name=self._exchange,
                        exchange_type="topic",
                        queue_name=self._queue,
                        routing_key=routing_key,
                    )
                )
            )
            adapter = AsyncAdapter(
                rabbitmq_connection_data=self._connection,
                configuration=conf,
                loop=self._loop,
                logger=self._logger)
            self._adapters[routing_key] = adapter
        return self._adapters[routing_key]

    def subscribe(self, topic, callback):
        if self._connected:
            self._subscribe(topic, callback)
        else:
            self._pending_subscriptions.append((topic, callback))

    def _subscribe(self, topic, callback):
        assert self._connected, "Not connected"
        assert self._stream_adapter, "Not connected"
        self._callbacks[topic] = callback
        conf = dict(
            exchange_name=self._exchange,
            exchange_type="topic",
            queue_name=self._queue,
            routing_key=topic,
        )
        self._stream_adapter.add_consumer(conf)

    async def _handle(self, logger, message):
        body = message.body.decode()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON Request: %s" % body, exc_info=True)
            return
        topic = message.routing_key
        fn = self._callbacks.get(topic)
        if fn:
            try:
                await fn(topic, data)
            except Exception:
                logger.error(
                    "Error handling event: %s" % topic,
                    exc_info=True)

