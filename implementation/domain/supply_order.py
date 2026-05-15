import decimal
import datetime
import enum


class SupplyOrderStatus(enum.Enum):
    CREATED = "created"
    DELIVERED = "delivered"
    IN_COMPLAINT = "in_complaint"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    CANCELED = "canceled"


class SupplyOrder:
    def __init__(
        self,
        id: int,
        supplier_id: int,
        total: decimal.Decimal,
        status: SupplyOrderStatus = SupplyOrderStatus.CREATED,
        realization_time: datetime.datetime | None = None,
        created_at: datetime.datetime | None = None,
        delivered_at: datetime.datetime | None = None,
        completed_at: datetime.datetime | None = None,
        in_complaint_at: datetime.datetime | None = None,
    ):
        self.id = id
        self.supplier_id = supplier_id
        self.total = total
        self.status = status
        self.realization_time = realization_time
        self.created_at = created_at
        self.delivered_at = delivered_at
        self.completed_at = completed_at
        self.in_complaint_at = in_complaint_at

    def mark_as_in_complaint(self):
        self.status = SupplyOrderStatus.IN_COMPLAINT
        self.in_complaint_at = datetime.datetime.now()

    def mark_as_resolved(self):
        self.status = SupplyOrderStatus.RESOLVED
        self.completed_at = datetime.datetime.now()

    def mark_as_rejected(self):
        self.status = SupplyOrderStatus.REJECTED

    def mark_as_canceled(self):
        self.status = SupplyOrderStatus.CANCELED

    def transition_to_delivered(self):
        self.status = SupplyOrderStatus.DELIVERED
        self.delivered_at = datetime.datetime.now()

    def transition_to_in_complaint(self):
        self.status = SupplyOrderStatus.IN_COMPLAINT
        self.in_complaint_at = datetime.datetime.now()


class SuppliedFlower:
    def __init__(self, supply_order_id: int, flower_id: int, quantity: int):
        self.supply_order_id = supply_order_id
        self.flower_id = flower_id
        self.quantity = quantity
