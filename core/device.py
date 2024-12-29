import random
import numpy as np
from enum import Enum
from core.base import Energy, Schedule, EnergyMode


class DeviceMode(Enum):
    ONCE = 'once'  # only execute once, no time limit
    PERSIST = 'persist'  # keep executing
    IMMEDIATE = 'immediate'  # only executed once, but must be executed immediately


class Device(Energy):
    def __init__(self, device_id, device_type):
        super().__init__()
        self.device_id = device_id
        self.device_type = device_type

    def supply(self, datetime: Schedule):
        return 0

    def demand(self, datetime: Schedule):
        return 0

    def mode(self):
        pass


class SolarPanels(Device):
    def __init__(self, device_id):
        super().__init__(device_id, "solar panels")
        self.init()

    def init(self):
        self._energy = np.full((7, 24), 100)

    def supply(self, datetime: Schedule):
        return self._energy[datetime.weekday, datetime.hour]

    def mode(self):
        return DeviceMode.PERSIST

    def energy_mode(self):
        return EnergyMode.Producer

    def discharge(self, datetime: Schedule, amount):
        diff = min(self._energy[datetime.weekday][datetime.hour], amount)
        self._energy[datetime.weekday][datetime.hour] -= diff

        return diff


class EV(Device):
    def __init__(self, device_id):
        super().__init__(device_id, "electric vehicles")
        self.init()

    def init(self):
        self._demand = 500

    def demand(self, _):
        return self._demand

    def mode(self):
        return DeviceMode.ONCE

    def energy_mode(self):
        return EnergyMode.Consumer

    def charge(self, datetime: Schedule, amount):
        diff = min(self._demand, amount)
        self._demand -= diff

        return diff


class Appliances(Device):
    def __init__(self, device_id):
        super().__init__(device_id, "appliances")
        self.init()

    def init(self):
        self._demand = np.random.randint(20, 31, size=(7, 24))

    def demand(self, datetime: Schedule):
        return self._demand[datetime.weekday][datetime.hour]

    def mode(self):
        return DeviceMode.PERSIST

    def energy_mode(self):
        return EnergyMode.Consumer

    def charge(self, datetime: Schedule, amount):
        diff = min(self._demand, amount)
        self._demand -= diff

        return diff


class Other(Device):
    def __init__(self, device_id, device_type="other"):
        super().__init__(device_id, device_type)
        self.init()

    def init(self):
        self._demand = random.randint(20, 100)

    def demand(self, _):
        return self._demand

    def mode(self):
        return DeviceMode.IMMEDIATE

    def energy_mode(self):
        return EnergyMode.Consumer

    def charge(self, datetime: Schedule, amount):
        diff = min(self._demand, amount)
        self._demand -= diff

        return diff
