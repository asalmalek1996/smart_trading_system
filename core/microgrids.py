from core.external_power_grid import ExternalPowerGrid
from core.device import Device, DeviceMode
from core.base import EnergyMode, Schedule


class ESS(Device):  # Energy storage system
    def __init__(self, cap):
        super().__init__('ESS', 'energy storage system')
        self._cap = cap

    def supply(self, _):
        return self._energy

    def charge(self, _, amount):
        self._energy = min(self._energy+amount, self._cap)  # no more than capacity

    def discharge(self, _, amount):
        diff = min(amount, self._energy)  # no less than 0
        self._energy -= diff

        return diff

    def mode(self):
        return DeviceMode.PERSIST

    def energy_mode(self):
        return EnergyMode.Producer | EnergyMode.Consumer


class PCC:  # Point of common coupling
    def __init__(self, name, external):
        self._name = name
        self._external = external
        self._record = []

    def exchange(self, amount):
        if amount < 0:
            return 0
        demand = self._external.allocate(self._name, amount)
        self._record.append(demand)
        return demand


class Microgrids:
    def __init__(self, name):
        self._ess = ESS(10000)
        self.ess_id = self._ess.device_id
        self.external = ExternalPowerGrid()
        self.external_pcc = PCC(name, self.external)
        self.DERs = {}  # distributed energy resources
        self.consumers = {}
        self.register(self._ess)

    def register(self, device: Device):
        if device.energy_mode() | EnergyMode.Producer == EnergyMode.Producer:
            self.DERs[device.device_id] = device
        if device.energy_mode() | EnergyMode.Consumer == EnergyMode.Consumer:
            self.consumers[device.device_id] = device

    def power_flow(self, src_id, dst_id, datetime: Schedule, amount):
        if src_id not in self.DERs or dst_id not in self.consumers:
            return 'device not found'
        producer = self.DERs[src_id]
        consumer = self.consumers[dst_id]
        flow = producer.discharge(datetime, amount)
        consumer.charge(datetime, flow)

        # power from src to dst
        print(f'{src_id} provide {flow} units of electricity energy to {dst_id}')

