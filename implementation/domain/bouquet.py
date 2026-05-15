import decimal
import datetime
import enum


class Flower:
    def __init__(
        self, id: int, price: decimal.Decimal, name: str, photo_url: str, quantity: int
    ):
        self.id = id
        self.price = price
        self.name = name
        self.photo_url = photo_url
        self.quantity = quantity


class BouquetStatus(enum.Enum):
    CREATED = "created"
    PREPARED = "prepared"
    EXPIRED = "expired"
    SOLD = "sold"


class Bouquet:
    def __init__(
        self,
        id: int,
        status: BouquetStatus,
        total: decimal.Decimal,
        created_at: datetime.datetime,
        prepared_at: datetime.datetime | None,
        completed_at: datetime.datetime | None,
        name: str = "",
        description: str = "",
    ):
        self.id = id
        self.status = status
        self.total = total
        self.created_at = created_at
        self.prepared_at = prepared_at
        self.completed_at = completed_at
        self.name = name
        self.description = description

    def is_available(self):
        return self.status == BouquetStatus.PREPARED


class UsedFlower:
    def __init__(self, flower_id: int, bouquet_id: int, quantity: int):
        self.flower_id = flower_id
        self.bouquet_id = bouquet_id
        self.quantity = quantity