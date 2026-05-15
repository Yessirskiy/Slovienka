class CustomerOrderRepo:
    _store = {}  # class-level: survives multiple instantiations

    def __init__(self):
        self.orders = CustomerOrderRepo._store

    def get_order_by_id(self, order_id: int):
        return self.orders.get(order_id, None)

    def get_all_orders(self):
        return [order for _, order in self.orders.items()]

    def save(self, order):
        self.orders[order.id] = order
        return order

    def get_orders_by_customer_id(self, customer_id: int):
        return [o for o in self.orders.values() if o.customer_id == customer_id]

    def next_id(self) -> int:
        return max(self.orders.keys(), default=-1) + 1