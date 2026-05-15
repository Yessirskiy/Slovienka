import sys, os, datetime, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.customer_order import CustomerOrderStatus

from repository.customer_order_repo import CustomerOrderRepo
from repository.delivery_repo import DeliveryRepo

from application.customer_order_handlers import (
    CreateCustomerOrderHandler,
    GetCustomerOrderHandler,
    StartPreparingCustomerOrderHandler,
    FinishPreparingCustomerOrderHandler,
)

ADDRESS = "Kvetná 12, Bratislava"
FLORIST_ID = 2  # id=2 is Florista in mock data


def _future_datetimes(days=3):
    base = datetime.datetime.now() + datetime.timedelta(days=days)
    return (
        base.replace(hour=9,  minute=0, second=0, microsecond=0),
        base.replace(hour=12, minute=0, second=0, microsecond=0),
    )


def _reset_repos():
    CustomerOrderRepo._store.clear()
    DeliveryRepo._store.clear()


def _create_test_order(customer_id=0, bouquet_id=0):
    from_dt, to_dt = _future_datetimes()
    return CreateCustomerOrderHandler().handler(
        customer_id=customer_id,
        bouquet_id=bouquet_id,
        address=ADDRESS,
        from_datetime=from_dt,
        to_datetime=to_dt,
    )


def _get_order(customer_id, order_id):
    return GetCustomerOrderHandler().handler(customer_id=customer_id, order_id=order_id)


# ══════════════════════════════════════════════════════════════════════════════
class TestStartPreparingCustomerOrder(unittest.TestCase):
    """
    AT-01  Kvetinár začína prípravu objednávky

    StartPreparingCustomerOrderHandler overuje komponentov a nastaví stav PREPARING.
    """

    def setUp(self):
        _reset_repos()
        self.handler = StartPreparingCustomerOrderHandler()

    # ── AT-01-A: úspešné spustenie prípravy ───────────────────────────────────
    def test_start_sets_status_to_preparing(self):
        """
        GIVEN: objednávka v stave CREATED
        WHEN:  StartPreparingCustomerOrderHandler je zavolaný s components_available=True
        THEN:  status sa zmení na PREPARING
        """
        order = _create_test_order()
        result = self.handler.handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=True,
        )

        self.assertEqual(result["status"], "success")
        updated = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(updated.status, CustomerOrderStatus.PREPARING)

    def test_start_assigns_florist_to_order(self):
        """
        WHEN:  spustenie prípravy prebehne úspešne
        THEN:  order.florosita_id == florist_id
        """
        order = _create_test_order()
        self.handler.handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=True,
        )

        updated = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(updated.florosita_id, FLORIST_ID)

    # ── AT-01-B: chýbajúce komponenty ─────────────────────────────────────────
    def test_missing_components_returns_failed_status(self):
        """
        GIVEN: components_available=False
        THEN:  handler vráti {"status": "failed", "reason": "Missing components"}
              a objednávka zostane v stave CREATED
        """
        order = _create_test_order()
        result = self.handler.handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=False,
            missing_components=["Ruže", "Zelené listy"],
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "Missing components")

        updated = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(updated.status, CustomerOrderStatus.CREATED)

    def test_missing_components_recorded_on_order(self):
        """
        WHEN:  missing_components sú zadané
        THEN:  order.missing_components obsahuje zadaný zoznam
        """
        missing = ["Ruže", "Zelené listy"]
        order = _create_test_order()
        self.handler.handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=False,
            missing_components=missing,
        )

        updated = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(updated.missing_components, missing)

    # ── AT-01-C: validácia kvetinára ───────────────────────────────────────────
    def test_customer_as_florist_raises(self):
        """id=0 je Customer, nie Florista → ValueError obsahuje 'florist_id'"""
        order = _create_test_order()
        with self.assertRaises(ValueError) as ctx:
            self.handler.handler(florist_id=0, order_id=order.id, components_available=True)
        self.assertIn("florist_id", str(ctx.exception))

    def test_nonexistent_florist_raises(self):
        """id=9999 neexistuje → ValueError"""
        order = _create_test_order()
        with self.assertRaises(ValueError):
            self.handler.handler(florist_id=9999, order_id=order.id, components_available=True)

    def test_nonexistent_order_raises(self):
        """order_id=9999 neexistuje → ValueError obsahuje 'order_id'"""
        with self.assertRaises(ValueError) as ctx:
            self.handler.handler(florist_id=FLORIST_ID, order_id=9999, components_available=True)
        self.assertIn("order_id", str(ctx.exception))


# ══════════════════════════════════════════════════════════════════════════════
class TestFinishPreparingCustomerOrder(unittest.TestCase):
    """
    AT-02  Kvetinár dokončí prípravu objednávky

    FinishPreparingCustomerOrderHandler nastaví stav PREPARED a spustí následné akcie.
    """

    def setUp(self):
        _reset_repos()
        self.start = StartPreparingCustomerOrderHandler()
        self.finish = FinishPreparingCustomerOrderHandler()

    def _start_order(self, customer_id=0, bouquet_id=0):
        order = _create_test_order(customer_id=customer_id, bouquet_id=bouquet_id)
        self.start.handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=True,
        )
        return order

    # ── AT-02-A: úspešné dokončenie prípravy ──────────────────────────────────
    def test_finish_sets_status_to_prepared(self):
        """
        GIVEN: objednávka v stave PREPARING
        WHEN:  FinishPreparingCustomerOrderHandler je zavolaný
        THEN:  status sa zmení na PREPARED
        """
        order = self._start_order()
        result = self.finish.handler(florist_id=FLORIST_ID, order_id=order.id)

        self.assertEqual(result["status"], "success")
        updated = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(updated.status, CustomerOrderStatus.PREPARED)

    def test_finish_sets_prepared_at_timestamp(self):
        """
        WHEN:  príprava je dokončená
        THEN:  order.prepared_at je nastavené (nie None)
        """
        order = self._start_order()
        self.finish.handler(florist_id=FLORIST_ID, order_id=order.id)

        updated = _get_order(customer_id=0, order_id=order.id)
        self.assertIsNotNone(updated.prepared_at)

    def test_finish_keeps_florist_assigned(self):
        """Kvetinár priradený pri štarte zostane na objednávke po dokončení."""
        order = self._start_order()
        self.finish.handler(florist_id=FLORIST_ID, order_id=order.id)

        updated = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(updated.florosita_id, FLORIST_ID)

    # ── AT-02-B: validácia stavu ───────────────────────────────────────────────
    def test_finish_on_created_order_raises(self):
        """
        GIVEN: objednávka v stave CREATED (Start nebol zavolaný)
        WHEN:  FinishPreparingCustomerOrderHandler je zavolaný
        THEN:  ValueError — vyžaduje stav PREPARING
        """
        order = _create_test_order()
        with self.assertRaises(ValueError) as ctx:
            self.finish.handler(florist_id=FLORIST_ID, order_id=order.id)
        self.assertIn("PREPARING", str(ctx.exception))

    def test_finish_invalid_florist_raises(self):
        """id=0 je Customer → ValueError obsahuje 'florist_id'"""
        order = self._start_order()
        with self.assertRaises(ValueError) as ctx:
            self.finish.handler(florist_id=0, order_id=order.id)
        self.assertIn("florist_id", str(ctx.exception))

    def test_finish_nonexistent_order_raises(self):
        """order_id=9999 neexistuje → ValueError obsahuje 'order_id'"""
        with self.assertRaises(ValueError) as ctx:
            self.finish.handler(florist_id=FLORIST_ID, order_id=9999)
        self.assertIn("order_id", str(ctx.exception))


# ══════════════════════════════════════════════════════════════════════════════
class TestFullProcessingFlow(unittest.TestCase):
    """
    AT-03  Celý tok spracovania objednávky

    Overuje sekvenciu CREATED → PREPARING → PREPARED cez oba handlery.
    """

    def setUp(self):
        _reset_repos()

    def test_full_flow_created_to_prepared(self):
        """
        GIVEN: nová objednávka v stave CREATED
        WHEN:  Start → Finish sú zavolané v správnom poradí
        THEN:  objednávka skončí v stave PREPARED s nastaveným prepared_at
        """
        order = _create_test_order()

        start_result = StartPreparingCustomerOrderHandler().handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=True,
        )
        self.assertEqual(start_result["status"], "success")

        mid = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(mid.status, CustomerOrderStatus.PREPARING)

        finish_result = FinishPreparingCustomerOrderHandler().handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
        )
        self.assertEqual(finish_result["status"], "success")

        final = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(final.status, CustomerOrderStatus.PREPARED)
        self.assertIsNotNone(final.prepared_at)

    def test_missing_components_then_retry_succeeds(self):
        """
        GIVEN: prvý pokus zlyhá pre chýbajúce komponenty
        WHEN:  druhý pokus prebehne s components_available=True
        THEN:  objednávka sa úspešne posunie do stavu PREPARING
        """
        order = _create_test_order()
        start = StartPreparingCustomerOrderHandler()

        first = start.handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=False,
            missing_components=["Ruže"],
        )
        self.assertEqual(first["status"], "failed")

        second = start.handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=True,
        )
        self.assertEqual(second["status"], "success")

        updated = _get_order(customer_id=0, order_id=order.id)
        self.assertEqual(updated.status, CustomerOrderStatus.PREPARING)

    def test_cannot_finish_twice(self):
        """
        WHEN:  Finish je zavolaný dvakrát na rovnakej objednávke
        THEN:  druhý pokus zlyhá — objednávka nie je v stave PREPARING
        """
        order = _create_test_order()
        StartPreparingCustomerOrderHandler().handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
            components_available=True,
        )
        FinishPreparingCustomerOrderHandler().handler(
            florist_id=FLORIST_ID,
            order_id=order.id,
        )

        with self.assertRaises(ValueError):
            FinishPreparingCustomerOrderHandler().handler(
                florist_id=FLORIST_ID,
                order_id=order.id,
            )


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
