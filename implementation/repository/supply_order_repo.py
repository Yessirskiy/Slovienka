import decimal
import datetime

from domain.supply_order import SupplyOrder, SupplyOrderStatus, SuppliedFlower

NOW = datetime.datetime(2026, 4, 7)


class SupplyOrderRepo:
    _store = {}

    def __init__(self):
        if not SupplyOrderRepo._store:
            SupplyOrderRepo._store.update({
                0: SupplyOrder(
                    0, supplier_id=0, total=decimal.Decimal("320.00"),
                    status=SupplyOrderStatus.DELIVERED,
                    realization_time=datetime.datetime(2026, 3, 20),
                    created_at=datetime.datetime(2026, 3, 15),
                    delivered_at=datetime.datetime(2026, 3, 21),
                ),
                1: SupplyOrder(
                    1, supplier_id=1, total=decimal.Decimal("540.50"),
                    status=SupplyOrderStatus.CREATED,
                    realization_time=datetime.datetime(2026, 4, 10),
                    created_at=NOW,
                ),
                2: SupplyOrder(
                    2, supplier_id=2, total=decimal.Decimal("185.00"),
                    status=SupplyOrderStatus.IN_COMPLAINT,
                    realization_time=datetime.datetime(2026, 3, 28),
                    created_at=datetime.datetime(2026, 3, 22),
                    delivered_at=datetime.datetime(2026, 3, 29),
                    in_complaint_at=datetime.datetime(2026, 4, 1),
                ),
                3: SupplyOrder(
                    3, supplier_id=0, total=decimal.Decimal("97.00"),
                    status=SupplyOrderStatus.CANCELED,
                    realization_time=datetime.datetime(2026, 4, 5),
                    created_at=datetime.datetime(2026, 3, 30),
                ),
            })
        self.orders = SupplyOrderRepo._store

    def get_order_by_id(self, id: int) -> SupplyOrder | None:
        return self.orders.get(id, None)

    def get_all_orders(self) -> list[SupplyOrder]:
        return list(self.orders.values())

    def save(self, order: SupplyOrder) -> SupplyOrder:
        self.orders[order.id] = order
        return order

    def next_id(self) -> int:
        return max(self.orders.keys(), default=-1) + 1


class SuppliedFlowerRepo:
    def __init__(self):
        self.supplied_flowers = [
            SuppliedFlower(supply_order_id=0, flower_id=0, quantity=50),
            SuppliedFlower(supply_order_id=0, flower_id=1, quantity=30),
            SuppliedFlower(supply_order_id=1, flower_id=2, quantity=40),
            SuppliedFlower(supply_order_id=1, flower_id=3, quantity=20),
            SuppliedFlower(supply_order_id=2, flower_id=4, quantity=60),
            SuppliedFlower(supply_order_id=3, flower_id=0, quantity=25),
        ]

    def get_by_order_id(self, supply_order_id: int) -> list[SuppliedFlower]:
        return [sf for sf in self.supplied_flowers if sf.supply_order_id == supply_order_id]

    def get_by_flower_id(self, flower_id: int) -> list[SuppliedFlower]:
        return [sf for sf in self.supplied_flowers if sf.flower_id == flower_id]
