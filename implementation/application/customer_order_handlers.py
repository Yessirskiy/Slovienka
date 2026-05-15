import datetime

from domain.delivery import Delivery
from domain.customer_order import CustomerOrder, PaymentMethod, CustomerOrderStatus
from domain.user import Customer, Florista

from repository.user_repo import UserRepo
from repository.customer_order_repo import CustomerOrderRepo
from repository.bouquet_repo import BouquetRepo
from repository.delivery_repo import DeliveryRepo

from application.flowers_handlers import CheckBouquetAvailabilityHandler


class ValidateCustomerOrderHandler:
    def handler(
        self,
        customer_id: int,
        bouquet_id: int,
        address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> dict:
        """Overí vstupné údaje novej objednávky a vráti zoznam chýb."""
        errors = []

        customer = UserRepo().get_user_by_id(customer_id)
        if customer is None or not isinstance(customer, Customer):
            errors.append("Invalid customer_id")

        if not address or not address.strip():
            errors.append("Address must not be empty")

        now = datetime.datetime.now()
        if from_datetime <= now:
            errors.append("Delivery start must be in the future")

        if to_datetime <= from_datetime:
            errors.append("Delivery end must be after delivery start")

        if not CheckBouquetAvailabilityHandler().handler(bouquet_id, quantity=1):
            errors.append("Bouquet is not available")

        return {"valid": len(errors) == 0, "errors": errors}


class CreateCustomerOrderHandler:
    def handler(
        self,
        customer_id: int,
        bouquet_id: int,
        address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
        payment_method: PaymentMethod = PaymentMethod.CASH,
    ):
        """Vytvorí novú zákaznícku objednávku spolu s doručením po úspešnej validácii."""
        validation = ValidateCustomerOrderHandler().handler(
            customer_id, bouquet_id, address, from_datetime, to_datetime
        )
        if not validation["valid"]:
            raise ValueError(validation["errors"])

        bouquet = BouquetRepo().get_bouquet_by_id(bouquet_id)

        order_repo = CustomerOrderRepo()
        order_id = order_repo.next_id()

        order = CustomerOrder(
            id=order_id,
            customer_id=customer_id,
            florosita_id=None,
            bouquet_id=bouquet_id,
            is_online=True,
            total=bouquet.total,
            payment_method=payment_method,
            created_at=datetime.datetime.now(),
        )

        delivery = Delivery(
            order_id=order_id,
            address=address,
            status="pending",
            from_datetime=from_datetime,
            to_datetime=to_datetime,
        )

        order_repo.save(order)
        DeliveryRepo().save(delivery)

        return order


class ListCustomerOrdersHandler:
    def handler(self, customer_id: int) -> list[CustomerOrder]:
        """Vráti zoznam všetkých objednávok daného zákazníka."""
        customer = UserRepo().get_user_by_id(customer_id)
        if customer is None or not isinstance(customer, Customer):
            raise ValueError("Invalid customer_id")

        return CustomerOrderRepo().get_orders_by_customer_id(customer_id)


class GetCustomerOrderHandler:
    def handler(self, customer_id: int, order_id: int) -> CustomerOrder:
        """Vráti konkrétnu objednávku zákazníka; overí, že objednávka mu patrí."""
        customer = UserRepo().get_user_by_id(customer_id)
        if customer is None or not isinstance(customer, Customer):
            raise ValueError("Invalid customer_id")

        order = CustomerOrderRepo().get_order_by_id(order_id)
        if order is None:
            raise ValueError("Invalid order_id")

        if order.customer_id != customer_id:
            raise ValueError("Order does not belong to this customer")

        return order


class ValidateEditCustomerOrderHandler:
    def handler(
        self,
        customer_id: int,
        order_id: int,
        address: str | None = None,
        from_datetime: datetime.datetime | None = None,
        to_datetime: datetime.datetime | None = None,
    ) -> dict:
        """Overí, či je možné upraviť objednávku so zadanými údajmi, a vráti zoznam chýb."""
        errors = []

        customer = UserRepo().get_user_by_id(customer_id)
        if customer is None or not isinstance(customer, Customer):
            errors.append("Invalid customer_id")
            return {"valid": False, "errors": errors}

        order = CustomerOrderRepo().get_order_by_id(order_id)
        if order is None:
            errors.append("Invalid order_id")
            return {"valid": False, "errors": errors}

        if order.customer_id != customer_id:
            errors.append("Order does not belong to this customer")
            return {"valid": False, "errors": errors}

        if order.status != CustomerOrderStatus.CREATED:
            errors.append("Order can only be edited in CREATED state")

        if address is not None and not address.strip():
            errors.append("Address must not be empty")

        now = datetime.datetime.now()
        if from_datetime is not None and from_datetime <= now:
            errors.append("Delivery start must be in the future")

        if to_datetime is not None:
            delivery = DeliveryRepo().get_delivery_by_order_id(order_id)
            ref_from = from_datetime if from_datetime is not None else (
                delivery.from_datetime if delivery else None
            )
            if ref_from is not None and to_datetime <= ref_from:
                errors.append("Delivery end must be after delivery start")

        return {"valid": len(errors) == 0, "errors": errors}


class EditCustomerOrderHandler:
    def handler(
        self,
        customer_id: int,
        order_id: int,
        address: str | None = None,
        from_datetime: datetime.datetime | None = None,
        to_datetime: datetime.datetime | None = None,
    ):
        """Upraví doručovacie údaje existujúcej objednávky po úspešnej validácii."""
        validation = ValidateEditCustomerOrderHandler().handler(
            customer_id, order_id, address, from_datetime, to_datetime
        )
        if not validation["valid"]:
            raise ValueError(validation["errors"])

        delivery = DeliveryRepo().get_delivery_by_order_id(order_id)
        if address is not None:
            delivery.address = address
        if from_datetime is not None:
            delivery.from_datetime = from_datetime
        if to_datetime is not None:
            delivery.to_datetime = to_datetime
        DeliveryRepo().update_delivery_by_order_id(order_id, delivery)


class StartPreparingCustomerOrderHandler:
    def handler(
        self,
        florist_id: int,
        order_id: int,
        components_available: bool,
        missing_components: list = None,
    ):
        """Spustí prípravu objednávky kvetinárom; ak chýbajú komponenty, zaznamená ich."""
        florist = UserRepo().get_user_by_id(florist_id)
        if florist is None or not isinstance(florist, Florista):
            raise ValueError("Invalid florist_id")

        order = CustomerOrderRepo().get_order_by_id(order_id)
        if order is None:
            raise ValueError("Invalid order_id")

        if not components_available:
            if missing_components:
                order.missing_components = missing_components
                CustomerOrderRepo().save(order)
            return {"status": "failed", "reason": "Missing components"}

        order.status = CustomerOrderStatus.PREPARING
        order.florosita_id = florist_id
        CustomerOrderRepo().save(order)

        return {"status": "success"}


class FinishPreparingCustomerOrderHandler:
    def handler(self, florist_id: int, order_id: int):
        """Dokončí prípravu objednávky, vygeneruje kód kuriéra a upozorní zákazníka."""
        florist = UserRepo().get_user_by_id(florist_id)
        if florist is None or not isinstance(florist, Florista):
            raise ValueError("Invalid florist_id")

        order = CustomerOrderRepo().get_order_by_id(order_id)
        if order is None:
            raise ValueError("Invalid order_id")

        if order.status != CustomerOrderStatus.PREPARING:
            raise ValueError("Order is not in PREPARING state")

        order.status = CustomerOrderStatus.PREPARED
        order.prepared_at = datetime.datetime.now()
        CustomerOrderRepo().save(order)

        self._generate_courier_code(order_id)
        self._send_customer_notification()
        self._inform_courier()

        return {"status": "success"}

    def _generate_courier_code(self, order_id: int):
        delivery = DeliveryRepo().get_delivery_by_order_id(order_id)
        if delivery:
            delivery.courier_code = (
                f"COURIER-{order_id}-{int(datetime.datetime.now().timestamp())}"
            )
            DeliveryRepo().update_delivery_by_order_id(order_id, delivery)

    def _send_customer_notification(self):
        pass

    def _inform_courier(self):
        pass


class GetOrderDeliveryHandler:
    def handler(self, order_id: int):
        """Vráti doručenie priradené k danej objednávke."""
        return DeliveryRepo().get_delivery_by_order_id(order_id)


class ListAllOrdersHandler:
    def handler(self, florist_id: int) -> list[CustomerOrder]:
        """Vráti zoznam všetkých objednávok; prístupné len pre kvetinára."""
        florist = UserRepo().get_user_by_id(florist_id)
        if florist is None or not isinstance(florist, Florista):
            raise ValueError("Invalid florist_id")
        return CustomerOrderRepo().get_all_orders()


class GetOrderHandler:
    def handler(self, florist_id: int, order_id: int) -> CustomerOrder:
        """Vráti konkrétnu objednávku; prístupné len pre kvetinára."""
        florist = UserRepo().get_user_by_id(florist_id)
        if florist is None or not isinstance(florist, Florista):
            raise ValueError("Invalid florist_id")
        order = CustomerOrderRepo().get_order_by_id(order_id)
        if order is None:
            raise ValueError("Invalid order_id")
        return order
