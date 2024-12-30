import copy
from core.microgrids import Microgrids
from core.base import Schedule
from application.base import Trade
from application.user import User
from application.base import MarketInformation
from core.external_power_grid import ExternalPowerGrid


class DSM:  # Demand side management
    def __init__(self, external: ExternalPowerGrid):
        self._market_information = {}
        self.external = external

    def market_information(self, datetime: Schedule):
        if (datetime.weekday, datetime.hour) in self._market_information:
            return self._market_information[(datetime.weekday, datetime.hour)]

        return self.predict_market(datetime)

    def predict_market(self, datetime: Schedule):
        predict = MarketInformation()
        if datetime.has_pre():
            # TODO: predict supply and demand
            pre_datetime = datetime.copy().pre()
            predict = self._market_information[(pre_datetime.weekday, pre_datetime.hour)]
        predict.external_price = self.external.curr_price(datetime)

        return predict

    def record_market(self, datetime: Schedule, trade_list: list[Trade]):
        data = MarketInformation()
        data.external_price = self.external.curr_price(datetime)
        if (datetime.weekday, datetime.hour) in self._market_information:
            data = self._market_information[(datetime.weekday, datetime.hour)]

        data.trade_list.extend(trade_list)
        for trade in trade_list:
            data.supply[trade.price] = data.supply.get(trade.price, 0) + trade.amount
            data.demand[trade.price] = data.demand.get(trade.price, 0) + trade.amount


class DMS:  # Distribution management systems
    def __init__(self, microgrids: Microgrids):
        self.microgrids = microgrids

    def distribute_energy(self, trade_list: list[Trade], datetime: Schedule):
        for trade in trade_list:
            self.microgrids.power_flow(trade.supplier_device_id, trade.consumer_device_id, datetime, trade.amount)


class TradingPlatform:
    def __init__(self, microgrids: Microgrids):
        self.microgrids = microgrids
        self.market_manager = DSM(self.microgrids.external)
        self.allocator = DMS(microgrids)
        self.users = {}

    def register_user(self, user: User):
        self.users[user.user_id] = user
        for device in user.device_list:
            self.microgrids.register(device)

    def handle(self, datetime: Schedule):
        self.market_manager.predict_market(datetime)  # predicting supply and demand

        round_number = 1
        while True:
            self.notify_market(datetime)  # notify user

            supply_list = self.get_supply_list()  # collect supply
            demand_list = self.get_demand_list()  # collect demand
            if len(demand_list) == 0 or len(supply_list) == 0:
                break

            trade_list = self.match_trades(supply_list, demand_list)  # trade matching
            self.allocator.distribute_energy(trade_list, datetime)  # distribute energy by trade

            self.market_manager.record_market(datetime, trade_list)  # record trade

            if round_number > 5:
                break
            round_number += 1

    def notify_market(self, datetime: Schedule):
        for user in self.users.values():
            user.update_market_information(datetime, self.market_manager.market_information(datetime))

    def get_supply_list(self):
        result = []
        for user in self.users.values():
            result.extend(user.get_supply())
        return result

    def get_demand_list(self):
        result = []
        for user in self.users.values():
            result.extend(user.get_demand())
        return result

    @staticmethod
    def match_trades(supply_list: list[Trade], demand_list: list[Trade]):
        supply_list = sorted(copy.deepcopy(supply_list), key=lambda x: x.price)
        demand_list = sorted(copy.deepcopy(demand_list), key=lambda x: x.price, reverse=True)
        trade_list = []
        while supply_list and demand_list:
            supply = supply_list[0]
            demand = demand_list[0]
            if supply.price <= demand.price:
                amount = min(supply.amount, demand.amount)
                price = (supply.price + demand.price) / 2

                trade_list.append(Trade(
                    amount=amount,
                    price=price,
                    supplier_id=supply.supplier_id,
                    supplier_device_id=supply.supplier_device_id,
                    consumer_id=demand.consumer_id,
                    consumer_device_id=demand.consumer_device_id
                ))
                supply.amount -= amount
                demand.amount -= amount
                if supply.amount == 0:
                    supply_list.pop(0)
                if demand.amount == 0:
                    demand_list.pop(0)
            else:
                break

        return trade_list
