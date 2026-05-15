from domain.bouquet import Bouquet
from repository.bouquet_repo import BouquetRepo, FlowerRepo, UsedFlowerRepo


class GetBouquetHandler:
    def handler(self, bouquet_id: int) -> Bouquet:
        """Vráti kyticu podľa jej identifikátora."""
        bouquet = BouquetRepo().get_bouquet_by_id(bouquet_id)
        if bouquet is None:
            raise ValueError("Invalid bouquet_id")
        return bouquet


class GetAvailableBouquetsHandler:
    def handler(self) -> list[Bouquet]:
        """Vráti zoznam všetkých dostupných kytíc."""
        return BouquetRepo().get_all_available()


class CheckBouquetAvailabilityHandler:
    def handler(self, bouquet_id: int, quantity: int) -> bool:
        """Overí, či je kytica dostupná v požadovanom množstve (vrátane skladových zásob kvetov)."""
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")

        bouquet = BouquetRepo().get_bouquet_by_id(bouquet_id)
        if bouquet is None or not bouquet.is_available():
            return False

        used_flowers = [
            uf for uf in UsedFlowerRepo().used_flowers
            if uf.bouquet_id == bouquet_id
        ]
        flower_repo = FlowerRepo()
        for uf in used_flowers:
            flower = flower_repo.get_flowers_by_id(uf.flower_id)
            if flower is None or flower.quantity < uf.quantity * quantity:
                return False

        return True
