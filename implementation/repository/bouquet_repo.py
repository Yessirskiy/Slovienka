import decimal
from domain.bouquet import Flower, Bouquet, BouquetStatus, UsedFlower
import datetime

NOW = datetime.datetime(2026, 4, 7)


class FlowerRepo:
    def __init__(self):
        self.flowers = {
            0: Flower(0, decimal.Decimal("5.00"), "Tulipán",    "https://slovienka.sk/photos/0", 10),
            1: Flower(1, decimal.Decimal("7.00"), "Ruža",       "https://slovienka.sk/photos/1", 10),
            2: Flower(2, decimal.Decimal("4.00"), "Narcis",     "https://slovienka.sk/photos/2", 15),
            3: Flower(3, decimal.Decimal("6.00"), "Orchidea",   "https://slovienka.sk/photos/3", 8),
            4: Flower(4, decimal.Decimal("3.50"), "Slnečnica",  "https://slovienka.sk/photos/4", 20),
        }

    def get_flowers_by_id(self, id: int):
        return self.flowers.get(id, None)


class UsedFlowerRepo:
    def __init__(self):
        self.used_flowers = {UsedFlower(0, 0, 5), UsedFlower(1, 0, 5)}


class BouquetRepo:
    def __init__(self):
        self.bouquets = {
            0: Bouquet(0, BouquetStatus.PREPARED,   decimal.Decimal("60.00"), NOW, None, None,
                       name="Romantická ruža",
                       description="Klasická červená ruža s gypsofiliou – ideálna na výročia"),
            1: Bouquet(1, BouquetStatus.PREPARED,   decimal.Decimal("34.90"), NOW, None, None,
                       name="Jarná radosť",
                       description="Farebná zmes tulipánov a narcisov plná svežosti"),
            2: Bouquet(2, BouquetStatus.PREPARED,   decimal.Decimal("49.00"), NOW, None, None,
                       name="Luxusná orchidea",
                       description="Elegantná biela orchidea v dizajnovom kvetináči"),
            3: Bouquet(3, BouquetStatus.PREPARED,   decimal.Decimal("27.50"), NOW, None, None,
                       name="Letný úsmev",
                       description="Veselá kytica slnečníc a margarét – žltá energia leta"),
            4: Bouquet(4, BouquetStatus.PREPARED,   decimal.Decimal("42.00"), NOW, None, None,
                       name="Pastelový sen",
                       description="Jemné ružové a biele kvety – krásny darček pre každú ženu"),
            5: Bouquet(5, BouquetStatus.PREPARED,   decimal.Decimal("55.00"), NOW, None, None,
                       name="Svadobná elegancia",
                       description="Biela pivónia s eukalyptom – svadobná kytica bez kompromisov"),
            6: Bouquet(6, BouquetStatus.PREPARED,   decimal.Decimal("19.90"), NOW, None, None,
                       name="Mini kytička",
                       description="Malá, ale pôvabná kytica z lúčnych kvetov"),
            7: Bouquet(7, BouquetStatus.EXPIRED,    decimal.Decimal("38.00"), NOW, None, None,
                       name="Jesenné tóny",
                       description="Sušené kvety v zemitých farbách – nedostupné"),
        }

    def get_bouquet_by_id(self, id: int):
        return self.bouquets.get(id, None)

    def get_all_available(self):
        return [b for b in self.bouquets.values() if b.is_available()]