import logging
from . import handler
from . import formatter
from . import filter

LOG_EXCHANGE = 'log-test'#XXX
configured = False
def _no_reconfig(func):
    def wrapper(*args, **kwargs):
        global configured
        if configured:
            raise RuntimeError("Logging already configured")
        configured = True
        return func(*args, **kwargs)
    return wrapper

@_no_reconfig
def rmq_forward_config(host, port, username, password, agent_name):
    root = logging.getLogger()
    rmq_handler = handler.RabbitMQHandler(
        username=username,
        password=password,
        host=host,
        port=port,
        exchange=LOG_EXCHANGE,
        connection_params= dict(
            client_properties=dict(
                information = "Python logging handler",
                connection_name = agent_name
            )
        )
    )
    rmq_handler.setFormatter(formatter.JSONFormatter())
    rmq_handler.addFilter(filter.FieldFilter({'agent_name': agent_name}, True))
    root.addHandler(rmq_handler)
    root.setLevel(logging.INFO)
    report_logger = logging.getLogger('report')
    report_handler = handler.ReportHandler(
        'data/reports',
        agent_name)
    report_logger.setLevel(logging.INFO)
    report_logger.addHandler(report_handler)

@_no_reconfig
def compressed_rollover_config():
    rot_handler = handler.CompressedTimedRotatingFileHandler(
        'data/logs/trisigma-test.log',
        when='D',
        interval=1,
        backupCount=5)
    rot_handler.setFormatter(formatter.JSONFormatter())
    logger = logging.getLogger('default')
    logger.setLevel(logging.INFO)
    logger.addHandler(rot_handler)
