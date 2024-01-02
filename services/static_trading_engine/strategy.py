from trisigma.domain.trading import StrategyBehavior, StrategyExecutor, Trader

class StaticTrader(StrategyBehavior):

    STRATEGY_NAME = 'static'

    def on_start(self):
        if self.config['direction'] == 'long':
            self.buy(self.config['asset'], 1)
            self.say('Bought ' + self.config['asset'])
        elif self.config['direction'] == 'short':
            self.sell(self.config['asset'], 1)
            self.say('Sold ' + self.config['asset'])
        else:
            self.say(f"Insufficient specification: {self.config['direction']}")

class StaticTradingExecutor(StrategyExecutor):

    STRATEGY_NAME = StaticTrader.STRATEGY_NAME

    async def start(self):
        pass

    def spawn_instance(self, account_id, config):
        print('trader spawned', account_id, config)
        instance = StaticTrader(config, account_id, self.action_queue)
        self.instances.add_instance(instance, account_id)
        return instance._trader
    def remove_instance(self, trader_id):
        self.instances.remove_instance(trader_id)

