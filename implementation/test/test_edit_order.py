import sys, os, datetime, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.customer_order import CustomerOrder, CustomerOrderStatus, PaymentMethod

from repository.customer_order_repo import CustomerOrderRepo
from repository.delivery_repo import DeliveryRepo

from application.customer_order_handlers import (
    CreateCustomerOrderHandler,
    EditCustomerOrderHandler,
    ValidateEditCustomerOrderHandler,
    GetCustomerOrderHandler,
    ListCustomerOrdersHandler,
    StartPreparingCustomerOrderHandler,
)

ADDRESS = "Kvetná 12, Bratislava"


def _future_datetimes(days=3):
    base = datetime.datetime.now() + datetime.timedelta(days=days)
    return (
        base.replace(hour=9,  minute=0, second=0, microsecond=0),
        base.replace(hour=12, minute=0, second=0, microsecond=0),
    )


def _reset_repos():
    CustomerOrderRepo._store.clear()
    DeliveryRepo._store.clear()


def _create_test_order(customer_id=0, bouquet_id=0, payment=PaymentMethod.CASH) -> CustomerOrder:
    from_dt, to_dt = _future_datetimes()
    return CreateCustomerOrderHandler().handler(
        customer_id=customer_id,
        bouquet_id=bouquet_id,
        address=ADDRESS,
        from_datetime=from_dt,
        to_datetime=to_dt,
        payment_method=payment,
    )


# ══════════════════════════════════════════════════════════════════════════════
class TestEditOrderHappyPath(unittest.TestCase):
    """
    AT-01  Úspešná úprava objednávky (happy path)

    Zákazník môže zmeniť adresu doručenia a časové okno doručenia
    na existujúcej objednávke v stave CREATED.
    """

    def setUp(self):
        _reset_repos()
        self.handler = EditCustomerOrderHandler()

    # ── AT-01-A: adresa doručenia sa zmení ────────────────────────────────────
    def test_address_can_be_updated(self):
        """
        GIVEN: existujúca objednávka zákazníka (id=0)
        WHEN:  handler je zavolaný s novou adresou
        THEN:  žiadna výnimka — úprava prebehne úspešne
        """
        order = _create_test_order()
        self.handler.handler(
            customer_id=0,
            order_id=order.id,
            address="Nová ulica 99, Košice",
        )

    # ── AT-01-B: časové okno doručenia sa zmení ───────────────────────────────
    def test_datetimes_can_be_updated(self):
        """
        GIVEN: existujúca objednávka
        WHEN:  handler je zavolaný s novými from_datetime a to_datetime
        THEN:  žiadna výnimka — úprava prebehne úspešne
        """
        order = _create_test_order()
        new_base = datetime.datetime.now() + datetime.timedelta(days=7)
        self.handler.handler(
            customer_id=0,
            order_id=order.id,
            from_datetime=new_base.replace(hour=10, minute=0, second=0, microsecond=0),
            to_datetime=new_base.replace(hour=14, minute=0, second=0, microsecond=0),
        )

    # ── AT-01-C: pôvodná objednávka ostane nedotknutá ─────────────────────────
    def test_order_fields_unchanged_after_delivery_edit(self):
        """
        WHEN:  handler zmení len adresu doručenia
        THEN:  order.status, order.total, order.bouquet_id, order.id sa nezmenia
        """
        order = _create_test_order(bouquet_id=2)

        self.handler.handler(
            customer_id=0,
            order_id=order.id,
            address="Zmena adresy",
        )

        retrieved = GetCustomerOrderHandler().handler(customer_id=0, order_id=order.id)
        self.assertEqual(retrieved.id,         order.id)
        self.assertEqual(retrieved.status,     CustomerOrderStatus.CREATED)
        self.assertEqual(retrieved.bouquet_id, 2)
        self.assertEqual(retrieved.total,      order.total)

    # ── AT-01-D: updated datetime indirectly verified through re-validation ───
    def test_updated_from_datetime_reflected_in_subsequent_validation(self):
        """
        WHEN:  from_datetime je aktualizovaná
        THEN:  následná validácia používa novú hodnotu pri kontrole to_datetime

        Overuje perzistenciu from_datetime cez ValidateEditCustomerOrderHandler.
        """
        order = _create_test_order()
        new_base = datetime.datetime.now() + datetime.timedelta(days=10)
        new_from = new_base.replace(hour=10, minute=0, second=0, microsecond=0)
        new_to   = new_base.replace(hour=14, minute=0, second=0, microsecond=0)

        self.handler.handler(customer_id=0, order_id=order.id, from_datetime=new_from)

        # to_datetime before the new from_datetime must now fail validation
        result = ValidateEditCustomerOrderHandler().handler(
            customer_id=0,
            order_id=order.id,
            to_datetime=new_from - datetime.timedelta(hours=1),
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("end" in e.lower() for e in result["errors"]))

        # valid to_datetime after the new from_datetime must pass
        result_ok = ValidateEditCustomerOrderHandler().handler(
            customer_id=0,
            order_id=order.id,
            to_datetime=new_to,
        )
        self.assertTrue(result_ok["valid"])


# ══════════════════════════════════════════════════════════════════════════════
class TestEditOrderCustomerValidation(unittest.TestCase):
    """
    AT-02  Validácia zákazníka pri úprave objednávky

    Handler overuje, že customer_id odkazuje na existujúci Customer
    a že objednávka mu skutočne patrí.
    """

    def setUp(self):
        _reset_repos()
        self.handler = EditCustomerOrderHandler()

    def test_valid_customer_can_edit(self):
        """
        GIVEN: objednávka zákazníka id=0
        WHEN:  handler je zavolaný s customer_id=0
        THEN:  žiadna výnimka
        """
        order = _create_test_order(customer_id=0)
        try:
            self.handler.handler(customer_id=0, order_id=order.id, address="Nová adresa")
        except ValueError:
            self.fail("Platný zákazník (id=0) nesmie vyvolať ValueError")

    def test_nonexistent_customer_raises(self):
        """customer_id=9999 neexistuje → ValueError obsahuje 'customer_id'"""
        order = _create_test_order()
        with self.assertRaises(ValueError) as ctx:
            self.handler.handler(customer_id=9999, order_id=order.id, address="X")
        self.assertIn("customer_id", str(ctx.exception))

    def test_florista_cannot_edit_as_customer(self):
        """id=2 je Florista, nie Customer → ValueError obsahuje 'customer_id'"""
        order = _create_test_order()
        with self.assertRaises(ValueError) as ctx:
            self.handler.handler(customer_id=2, order_id=order.id, address="X")
        self.assertIn("customer_id", str(ctx.exception))

    def test_customer_cannot_edit_another_customers_order(self):
        """
        GIVEN: objednávka patrí zákazníkovi id=0
        WHEN:  zákazník id=1 sa ju pokúsi upraviť
        THEN:  ValueError — porušenie vlastníctva
        """
        order = _create_test_order(customer_id=0)
        with self.assertRaises(ValueError) as ctx:
            self.handler.handler(customer_id=1, order_id=order.id, address="X")
        self.assertIn("belong", str(ctx.exception).lower())


# ══════════════════════════════════════════════════════════════════════════════
class TestEditOrderOrderValidation(unittest.TestCase):
    """
    AT-03  Validácia objednávky pri úprave
    """

    def setUp(self):
        _reset_repos()
        self.handler = EditCustomerOrderHandler()

    def test_nonexistent_order_raises(self):
        """order_id=9999 neexistuje → ValueError obsahuje 'order_id'"""
        with self.assertRaises(ValueError) as ctx:
            self.handler.handler(customer_id=0, order_id=9999, address="X")
        self.assertIn("order_id", str(ctx.exception))

    def test_order_in_preparing_state_cannot_be_edited(self):
        """
        GIVEN: objednávka prešla do stavu PREPARING cez StartPreparingCustomerOrderHandler
        WHEN:  zákazník sa ju pokúsi upraviť
        THEN:  ValueError — úprava povolená iba v stave CREATED

        Overuje integráciu stavového automatu s edit handlerom.
        """
        order = _create_test_order()
        StartPreparingCustomerOrderHandler().handler(
            florist_id=2,
            order_id=order.id,
            components_available=True,
        )

        with self.assertRaises(ValueError) as ctx:
            self.handler.handler(customer_id=0, order_id=order.id, address="Nová adresa")
        self.assertIn("CREATED", str(ctx.exception))

    def test_past_from_datetime_rejected(self):
        """Delivery start v minulosti → ValidateEditCustomerOrderHandler vráti chybu."""
        order = _create_test_order()
        result = ValidateEditCustomerOrderHandler().handler(
            customer_id=0,
            order_id=order.id,
            from_datetime=datetime.datetime.now() - datetime.timedelta(hours=1),
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("future" in e.lower() for e in result["errors"]))

    def test_to_before_from_rejected(self):
        """to_datetime pred from_datetime → ValidateEditCustomerOrderHandler vráti chybu."""
        order = _create_test_order()
        base = datetime.datetime.now() + datetime.timedelta(days=5)
        result = ValidateEditCustomerOrderHandler().handler(
            customer_id=0,
            order_id=order.id,
            from_datetime=base.replace(hour=12, minute=0, second=0, microsecond=0),
            to_datetime=base.replace(hour=9,  minute=0, second=0, microsecond=0),
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("end" in e.lower() for e in result["errors"]))

    def test_empty_address_rejected(self):
        """Prázdna adresa → ValidateEditCustomerOrderHandler vráti chybu."""
        order = _create_test_order()
        result = ValidateEditCustomerOrderHandler().handler(
            customer_id=0,
            order_id=order.id,
            address="   ",
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("address" in e.lower() for e in result["errors"]))


# ══════════════════════════════════════════════════════════════════════════════
class TestListCustomerOrders(unittest.TestCase):
    """
    AT-04  ListCustomerOrdersHandler — filtrovanie objednávok podľa zákazníka
    """

    def setUp(self):
        _reset_repos()

    def test_returns_only_orders_for_given_customer(self):
        """
        GIVEN: zákazník id=0 má 2 objednávky, zákazník id=1 má 1 objednávku
        THEN:  ListCustomerOrdersHandler vráti správny počet pre každého
        """
        _create_test_order(customer_id=0)
        _create_test_order(customer_id=0)
        _create_test_order(customer_id=1)

        result = ListCustomerOrdersHandler().handler(customer_id=0)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(o.customer_id == 0 for o in result))

    def test_returns_empty_list_for_customer_with_no_orders(self):
        """Zákazník bez objednávok → prázdny zoznam (nie None, nie výnimka)"""
        _create_test_order(customer_id=0)
        result = ListCustomerOrdersHandler().handler(customer_id=1)
        self.assertEqual(result, [])

    def test_does_not_return_other_customers_orders(self):
        """Zákazník nikdy nevidí objednávky iného zákazníka."""
        _create_test_order(customer_id=0)
        order_1 = _create_test_order(customer_id=1)

        ids = [o.id for o in ListCustomerOrdersHandler().handler(customer_id=0)]
        self.assertNotIn(order_1.id, ids)

    def test_invalid_customer_raises(self):
        """Neexistujúci zákazník → ValueError"""
        with self.assertRaises(ValueError):
            ListCustomerOrdersHandler().handler(customer_id=9999)


# ══════════════════════════════════════════════════════════════════════════════
class TestEditOrderPersistence(unittest.TestCase):
    """
    AT-05  Perzistencia úprav — objednávka zostane prístupná po úprave
    """

    def setUp(self):
        _reset_repos()
        self.handler = EditCustomerOrderHandler()

    def test_order_retrievable_after_edit(self):
        """
        WHEN:  objednávka je upravená
        THEN:  GetCustomerOrderHandler ju stále vráti s pôvodným ID
        """
        order = _create_test_order()
        self.handler.handler(customer_id=0, order_id=order.id, address="Persistovaná ulica 1")

        retrieved = GetCustomerOrderHandler().handler(customer_id=0, order_id=order.id)
        self.assertEqual(retrieved.id, order.id)

    def test_edit_does_not_create_duplicate_order(self):
        """
        WHEN:  objednávka je upravená
        THEN:  celkový počet objednávok zákazníka ostane 1
        """
        order = _create_test_order()
        self.assertEqual(len(ListCustomerOrdersHandler().handler(customer_id=0)), 1)

        self.handler.handler(customer_id=0, order_id=order.id, address="Iná adresa")

        self.assertEqual(len(ListCustomerOrdersHandler().handler(customer_id=0)), 1)

    def test_multiple_sequential_edits_all_accepted(self):
        """Viacnásobné úpravy rovnakej objednávky sú akceptované."""
        order = _create_test_order()
        base = datetime.datetime.now() + datetime.timedelta(days=5)

        self.handler.handler(customer_id=0, order_id=order.id, address="Adresa 1")
        self.handler.handler(customer_id=0, order_id=order.id, address="Adresa 2")
        self.handler.handler(
            customer_id=0,
            order_id=order.id,
            from_datetime=base.replace(hour=8,  minute=0, second=0, microsecond=0),
            to_datetime=base.replace(hour=11, minute=0, second=0, microsecond=0),
        )

        retrieved = GetCustomerOrderHandler().handler(customer_id=0, order_id=order.id)
        self.assertEqual(retrieved.id, order.id)
        self.assertEqual(retrieved.status, CustomerOrderStatus.CREATED)


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
