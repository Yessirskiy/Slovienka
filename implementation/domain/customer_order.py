import decimal
import datetime
import enum


class PaymentMethod(enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    ONLINE_PAYMENT = "online_payment"


class CustomerOrderStatus(enum.Enum):
    CREATED = "created"
    PREPARING = "preparing"
    PREPARED = "prepared"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class CustomerOrder:
    def __init__(
        self,
        id: int,
        customer_id: int | None,
        florosita_id: int | None,
        bouquet_id: int,
        is_online: bool,
        total: decimal.Decimal,
        payment_method: PaymentMethod = PaymentMethod.CASH,
        status: CustomerOrderStatus = CustomerOrderStatus.CREATED,
        created_at: datetime.datetime | None = None,
        prepared_at: datetime.datetime | None = None,
        completed_at: datetime.datetime | None = None,
        delivered_at: datetime.datetime | None = None,
        missing_components: list[str] | None = None,
    ):
        self.id = id
        self.customer_id = customer_id
        self.florosita_id = florosita_id
        self.bouquet_id = bouquet_id
        self.is_online = is_online
        self.total = total
        self.payment_method = payment_method
        self.status = status
        self.created_at = created_at
        self.prepared_at = prepared_at
        self.completed_at = completed_at
        self.delivered_at = delivered_at
        self.missing_components = missing_components or []
