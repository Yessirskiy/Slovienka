import datetime


class Delivery:
    def __init__(
        self,
        order_id: int,
        address: str,
        status: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
        courier_code: str | None = None,
    ):
        self.order_id = order_id
        self.address = address
        self.status = status
        self.from_datetime = from_datetime
        self.to_datetime = to_datetime
        self.courier_code = courier_code
