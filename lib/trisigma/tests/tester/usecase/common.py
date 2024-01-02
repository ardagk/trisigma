from tests.util import statics

# Test Result Container
class TestResultContainer:

    __test__ = False

    def __init__(self, usecase, response=None, init_table=None):
        self.usecase = usecase
        self.table = self._get_generic_exposure_table()
        self.init_table = init_table
        self.resp = response
        if hasattr(self.usecase, 'brokerage_adapter'):
            self.cancelled_ids = self._get_cancelled_ids()
            self.modified_orders = self._get_modified_orders()
            self.submitted_orders = self._get_submitted_orders()
        if hasattr(self.usecase, 'order_repo'):
            self.status_updates = self._get_status_updates()

    def _get_generic_exposure_table(self):
        table = {}
        exposure_table = statics['exposure_table']
        for partition in exposure_table.exposures:
            table[partition] = {
                'alloc': exposure_table.exposures[partition].alloc,
                'open': exposure_table.exposures[partition].buffer,
                'weight': exposure_table.weights[partition]}
        return table

    def _get_cancelled_ids(self):
        cancelled_ids = [
            self.find_signal_id(call[1])
            for call in self.usecase.brokerage_adapter.calls
            if call[0] == 'cancel_order']
        return cancelled_ids

    def find_signal_id(self, order_ref):
        for val in self.init_table.values(): #pyright: ignore
            for key, item in val['open'].items():
                if item['ref'] == order_ref:
                    return key

    def _get_modified_orders(self):
        modified_orders = [
            list(call[1])
            for call in self.usecase.brokerage_adapter.calls
            if call[0] == 'modify_order']
        for order in modified_orders:
            order[0] = self.find_signal_id(order[0])
        modified_orders = [
            tuple(order) for order in modified_orders]
        return modified_orders

    def _get_submitted_orders(self):
        submitted_orders = [
            (call[1][0], call[1][1], call[1][2],
             call[1][3].get('order_type'), call[1][3].get('price'))
            for call in self.usecase.brokerage_adapter.calls
            if call[0] == 'place_order']
        return submitted_orders

    def _get_status_updates(self):
        stat_updates = [
            call[1] for call in self.usecase.order_repo.calls
            if call[0] == 'update_order_status']
        return stat_updates
