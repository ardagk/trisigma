from trisigma.domain.brokerage import OrderRepository

class MockOrderRepository(OrderRepository):

    def __init__(self):
        self.calls = []
        self.orders = []

    async def add_order(self, order):
        self.calls.append(('add_order', order))

    async def update_order_status(self, order_ref, status, price=None):
        self.calls.append(('update_order_status', (order_ref, status, price)))

    async def get_order(self, order_ref):
        raise NotImplementedError()

    async def search_orders(self, instance_id, order_status):
        raise NotImplementedError()
