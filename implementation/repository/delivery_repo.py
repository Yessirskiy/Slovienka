from domain.delivery import Delivery


class DeliveryRepo:
    _store = {}

    def __init__(self):
        self.deliveries = DeliveryRepo._store

    def get_delivery_by_order_id(self, order_id: int):
        return self.deliveries.get(order_id, None)

    def save(self, delivery: Delivery):
        self.deliveries[delivery.order_id] = delivery
        return delivery

    def update_delivery_by_order_id(self, order_id: int, delivery: Delivery):
        if order_id in self.deliveries:
            self.deliveries[order_id] = delivery
