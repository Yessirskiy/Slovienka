from domain.supplier import Supplier


class SupplierRepo:
    def __init__(self):
        self.suppliers = {
            0: Supplier(0, "info@kvetydunaj.sk",    "Kvety Dunaj s.r.o."),
            1: Supplier(1, "objednavky@florex.sk",  "Florex Slovakia a.s."),
            2: Supplier(2, "sklad@prirodakvet.sk",  "Príroda & Kvet"),
        }

    def get_supplier_by_id(self, id: int) -> Supplier | None:
        return self.suppliers.get(id, None)

    def get_all_suppliers(self) -> list[Supplier]:
        return list(self.suppliers.values())
