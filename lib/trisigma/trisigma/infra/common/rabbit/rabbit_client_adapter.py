import asyncio
from bunny_storm import AsyncAdapter, RabbitMQConnectionData
import uuid
import json
import logging
import sys
import time

class RabbitClientAdapter:

    _rpc_adapters = {}
    _callbacks = {}
    _queue = None
    _logger = None
    _connected = False

    def __init__(self, uri, exchange, queue_name=None, logger=None, loop=None):
        self._connection = self._prepare_connection(uri)
        self._queue = queue_name or uuid.uuid4().hex
        self._exchange = exchange + '-rpc'
        self._logger = logger or logging.getLogger(__name__)
        assert isinstance(self._logger, logging.Logger)
        self._loop = loop or asyncio.get_event_loop()

    async def connect(self):
        self._connected = True

    def _prepare_connection(self, uri):
        assert uri.startswith("amqp://")
        usr, pwd = uri.split("@")[0][len("amqp://"):].split(":")
        host, port = uri.split("@")[1].split("/")[0].split(":")
        vhost = uri.split("/")[-1]
        connection = RabbitMQConnectionData(
            host=host, port=port,
            username=usr, password=pwd, virtual_host=vhost)
        return connection

    def _get_rpc_adapter(self, route):    
        if route not in self._rpc_adapters:
            self._rpc_adapters[route] = self._prepare_rpc_adapter(route) 
        return self._rpc_adapters[route]

    def _prepare_rpc_adapter(self, route):
        assert self._logger
        conf = dict(
            publish=dict(
                publisher=dict(
                    exchange_name=self._exchange,
                    exchange_type="direct",
                    routing_key=route),
            ),
            receive=dict(
                receiver=dict(
                    exchange_name=self._exchange,
                    exchange_type="direct",
                    #queue_name=self._queue,
                    queue_name=uuid.uuid4().hex,
                )
            ),
        )
        adapter = AsyncAdapter(
            rabbitmq_connection_data=self._connection,
            configuration=conf,
            loop=self._loop,
            logger=self._logger)
        return adapter

    async def request(self, target, endpoint, params={}):
        assert self._logger
        req = dict(endpoint=endpoint, params=params)
        try:
            payload = json.dumps(req).encode()
        except Exception as e:
            self._logger.error("Error encoding request: %s" % e, exc_info=True)
            raise
        adapter = self._get_rpc_adapter(target)
        assert len(adapter.consumers.keys()) == 1
        recv_queue = list(adapter.consumers.keys())[0]
        try:
            resp = await adapter.rpc(
                body=payload,
                receive_queue=recv_queue,
                publish_exchange=self._exchange,
                ttl=100,
                publisher_max_retry_count=0,
                timeout=10)
        except Exception as e:
            self._logger.error('RPC call error: ' + str(e))
            return
        try:
            data = json.loads(resp.decode())
        except Exception as e:
            self._logger.error("Error decoding response: %s" % e, exc_info=True)
            raise
        assert data["status"] == "ok", data['message']
        return data["message"]

