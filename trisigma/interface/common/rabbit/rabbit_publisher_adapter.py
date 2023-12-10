import asyncio
from bunny_storm import AsyncAdapter, RabbitMQConnectionData
import logging
import json
import uuid

class RabbitPublisherAdapter:

    _connection = None
    _callbacks = {}
    _adapter = None

    def __init__(self, uri, exchange, publisher_name, queue_name=None, logger=None, loop=None):
        self._connection = self._prepare_connection(uri)
        self._publisher_name = publisher_name
        self._exchange = f"{exchange}-pubsub"
        self._queue_name = queue_name or uuid.uuid4().hex
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

    async def publish(self, topic, message):
        try:
            payload = json.dumps(message).encode()
        except Exception:
            self._logger.error("Invalid JSON message: %s" % str(message), exc_info=True)
            return
        try:
            assert self._adapter is not None, "Stream adapter not set"
            await self._adapter.publish(
                body=payload,
                exchange=self._exchange,
                routing_key=topic)
        except Exception:
            self._logger.error("Error publishing message: %s" % str(message), exc_info=True)

    async def start(self):
        self._adapter = self._prepare_stream_adapter()

    def _prepare_stream_adapter(self):
        assert self._connection is not None, "Connection not set"
        conf = dict(
            publish=dict(
                publisher=dict(
                    exchange_name=self._exchange,
                    exchange_type="topic",
                    routing_key=self._publisher_name),
            ),
        )
        adapter = AsyncAdapter(
            rabbitmq_connection_data=self._connection,
            configuration=conf,
            loop=self._loop,
            logger=self._logger)
        return adapter

