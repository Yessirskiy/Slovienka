import sys, os, datetime, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.customer_order import CustomerOrder, CustomerOrderStatus, PaymentMethod
from domain.bouquet import BouquetStatus

from repository.customer_order_repo import CustomerOrderRepo
from repository.delivery_repo import DeliveryRepo

from application.customer_order_handlers import (
    CreateCustomerOrderHandler,
    ListCustomerOrdersHandler,
    GetCustomerOrderHandler,
)
from application.flowers_handlers import (
    GetBouquetHandler,
    GetAvailableBouquetsHandler,
    CheckBouquetAvailabilityHandler,
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


# ══════════════════════════════════════════════════════════════════════════════
class TestCreateOrderHappyPath(unittest.TestCase):
    """
    AT-01  Úspešné vytvorenie objednávky (happy path)

    Pokrýva kroky 1-8 z activity diagramu.
    """

    def setUp(self):
        _reset_repos()
        self.handler = CreateCustomerOrderHandler()
        self.from_dt, self.to_dt = _future_datetimes()

    # ── AT-01-A: objednávka sa vytvorí a uloží ────────────────────────────────
    def test_order_is_created_and_persisted(self):
        """
        GIVEN: platný zákazník (id=0) a dostupná kytica (id=0)
        WHEN:  handler.handler() je zavolaný so správnymi parametrami
        THEN:  vráti CustomerOrder s CREATED stavom a je dostupná cez GetCustomerOrderHandler
        """
        order = self.handler.handler(
            customer_id=0,
            bouquet_id=0,
            address=ADDRESS,
            from_datetime=self.from_dt,
            to_datetime=self.to_dt,
            payment_method=PaymentMethod.CREDIT_CARD,
        )

        self.assertIsInstance(order, CustomerOrder)
        self.assertEqual(order.customer_id, 0)
        self.assertEqual(order.bouquet_id, 0)
        self.assertEqual(order.payment_method, PaymentMethod.CREDIT_CARD)
        self.assertEqual(order.status, CustomerOrderStatus.CREATED)

        retrieved = GetCustomerOrderHandler().handler(customer_id=0, order_id=order.id)
        self.assertEqual(retrieved.id, order.id)

    # ── AT-01-B: cena sa preberá z kytica.total ───────────────────────────────
    def test_order_total_matches_bouquet_price(self):
        """
        Triedy CustomerOrder.total a Bouquet.total musia byť konzistentné.
        """
        bouquet = GetBouquetHandler().handler(bouquet_id=0)
        order = self.handler.handler(
            customer_id=0,
            bouquet_id=0,
            address=ADDRESS,
            from_datetime=self.from_dt,
            to_datetime=self.to_dt,
        )
        self.assertEqual(order.total, bouquet.total)

    # ── AT-01-C: online flag ───────────────────────────────────────────────────
    def test_order_is_marked_as_online(self):
        order = self.handler.handler(
            customer_id=0,
            bouquet_id=0,
            address=ADDRESS,
            from_datetime=self.from_dt,
            to_datetime=self.to_dt,
        )
        self.assertTrue(order.is_online)

    # ── AT-01-D: všetky PaymentMethod hodnoty fungujú ─────────────────────────
    def test_all_payment_methods_accepted(self):
        """
        PaymentMethod enum má 4 hodnoty — všetky musia byť akceptované handlerom.
        """
        for method in PaymentMethod:
            _reset_repos()
            order = self.handler.handler(
                customer_id=0,
                bouquet_id=0,
                address=ADDRESS,
                from_datetime=self.from_dt,
                to_datetime=self.to_dt,
                payment_method=method,
            )
            self.assertEqual(
                order.payment_method,
                method,
                f"PaymentMethod.{method.name} nebol uložený správne",
            )


# ══════════════════════════════════════════════════════════════════════════════
class TestAvailabilityCheck(unittest.TestCase):
    """
    AT-02  «include» Overenie dostupnosti tovaru
    """

    def setUp(self):
        _reset_repos()
        self.from_dt, self.to_dt = _future_datetimes()

    def test_available_bouquet_passes(self):
        """Kytica so stavom PREPARED je dostupná."""
        bouquet = GetBouquetHandler().handler(bouquet_id=0)
        self.assertEqual(bouquet.status, BouquetStatus.PREPARED)
        self.assertTrue(CheckBouquetAvailabilityHandler().handler(bouquet_id=0, quantity=1))

    def test_available_bouquets_list_excludes_expired(self):
        """GetAvailableBouquetsHandler nesmie vrátiť kyty so stavom EXPIRED."""
        bouquets = GetAvailableBouquetsHandler().handler()
        for b in bouquets:
            self.assertNotEqual(b.status, BouquetStatus.EXPIRED)

    def test_unavailable_bouquet_raises(self):
        """
        GIVEN: kytica so stavom EXPIRED (id=7 v mock dátach)
        WHEN:  zákazník sa ju pokúsi objednať
        THEN:  ValueError obsahuje "not available"
        """
        self.assertFalse(CheckBouquetAvailabilityHandler().handler(bouquet_id=7, quantity=1))
        with self.assertRaises(ValueError) as ctx:
            CreateCustomerOrderHandler().handler(
                customer_id=0,
                bouquet_id=7,
                address=ADDRESS,
                from_datetime=self.from_dt,
                to_datetime=self.to_dt,
            )
        self.assertIn("not available", str(ctx.exception).lower())

    def test_nonexistent_bouquet_raises(self):
        """Neexistujúca kytica → ValueError"""
        with self.assertRaises(ValueError):
            CreateCustomerOrderHandler().handler(
                customer_id=0,
                bouquet_id=9999,
                address=ADDRESS,
                from_datetime=self.from_dt,
                to_datetime=self.to_dt,
            )


# ══════════════════════════════════════════════════════════════════════════════
class TestCustomerValidation(unittest.TestCase):
    """
    AT-03  Validácia zákazníka

    Handler overuje, že customer_id odkazuje na existujúci objekt typu Customer
    (nie Florista ani Curier).
    """

    def setUp(self):
        _reset_repos()
        self.from_dt, self.to_dt = _future_datetimes()

    def test_valid_customer_accepted(self):
        order = CreateCustomerOrderHandler().handler(
            customer_id=0,
            bouquet_id=0,
            address=ADDRESS,
            from_datetime=self.from_dt,
            to_datetime=self.to_dt,
        )
        self.assertEqual(order.customer_id, 0)

    def test_nonexistent_customer_raises(self):
        with self.assertRaises(ValueError) as ctx:
            CreateCustomerOrderHandler().handler(
                customer_id=9999,
                bouquet_id=0,
                address=ADDRESS,
                from_datetime=self.from_dt,
                to_datetime=self.to_dt,
            )
        self.assertIn("customer_id", str(ctx.exception))

    def test_florista_as_customer_raises(self):
        """id=2 je Florista (nie Customer) — handler musí odmietnuť."""
        with self.assertRaises(ValueError) as ctx:
            CreateCustomerOrderHandler().handler(
                customer_id=2,
                bouquet_id=0,
                address=ADDRESS,
                from_datetime=self.from_dt,
                to_datetime=self.to_dt,
            )
        self.assertIn("customer_id", str(ctx.exception))


# ══════════════════════════════════════════════════════════════════════════════
class TestOrderStatusLifecycle(unittest.TestCase):
    """
    AT-04  Stavový diagram CustomerOrder — počiatočný stav
    """

    def setUp(self):
        _reset_repos()
        self.from_dt, self.to_dt = _future_datetimes()

    def test_new_order_starts_in_created_state(self):
        order = CreateCustomerOrderHandler().handler(
            customer_id=0,
            bouquet_id=0,
            address=ADDRESS,
            from_datetime=self.from_dt,
            to_datetime=self.to_dt,
        )
        self.assertEqual(
            order.status,
            CustomerOrderStatus.CREATED,
            "Nová objednávka musí začínať v stave CREATED",
        )

    def test_all_status_transitions_exist_in_enum(self):
        """Všetky stavy definované v stavovom diagrame musia existovať v enum."""
        expected = {
            "CREATED", "PREPARING", "PREPARED",
            "IN_DELIVERY", "DELIVERED", "COMPLETED",
            "CANCELED", "REFUNDED",
        }
        actual = {s.name for s in CustomerOrderStatus}
        self.assertEqual(expected, actual, f"Chýbajúce stavy: {expected - actual}")


# ══════════════════════════════════════════════════════════════════════════════
class TestRepositoryPersistence(unittest.TestCase):
    """
    AT-05  Perzistencia — objednávka zostane dostupná pre Kvetinára
    """

    def setUp(self):
        _reset_repos()
        self.from_dt, self.to_dt = _future_datetimes()

    def test_order_visible_via_get_handler(self):
        order = CreateCustomerOrderHandler().handler(
            customer_id=0,
            bouquet_id=0,
            address=ADDRESS,
            from_datetime=self.from_dt,
            to_datetime=self.to_dt,
        )
        retrieved = GetCustomerOrderHandler().handler(customer_id=0, order_id=order.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, order.id)

    def test_multiple_orders_visible_via_list_handler(self):
        for cid in [0, 1]:
            CreateCustomerOrderHandler().handler(
                customer_id=cid,
                bouquet_id=0,
                address=ADDRESS,
                from_datetime=self.from_dt,
                to_datetime=self.to_dt,
            )
        self.assertEqual(len(ListCustomerOrdersHandler().handler(customer_id=0)), 1)
        self.assertEqual(len(ListCustomerOrdersHandler().handler(customer_id=1)), 1)


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
