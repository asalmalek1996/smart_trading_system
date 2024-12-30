from dataclasses import dataclass


@dataclass(frozen=True)
class Trade:
    amount: float
    price: float
    supplier_id: str = 0
    supplier_device_id: str = 0
    consumer_id: str = 0
    consumer_device_id: str = 0
