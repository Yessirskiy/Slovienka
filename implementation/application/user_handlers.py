from domain.user import Customer, Florista
from repository.user_repo import UserRepo


class ListCustomersHandler:
    def handler(self) -> list[Customer]:
        """Vráti zoznam všetkých zákazníkov."""
        return [u for u in UserRepo().users.values() if isinstance(u, Customer)]


class ListFloristsHandler:
    def handler(self) -> list[Florista]:
        """Vráti zoznam všetkých kvetinárov."""
        return [u for u in UserRepo().users.values() if isinstance(u, Florista)]


class GetCustomerHandler:
    def handler(self, customer_id: int) -> Customer:
        """Vráti zákazníka podľa jeho identifikátora."""
        user = UserRepo().get_user_by_id(customer_id)
        if user is None or not isinstance(user, Customer):
            raise ValueError("Invalid customer_id")
        return user


class GetFloristHandler:
    def handler(self, florist_id: int) -> Florista:
        """Vráti kvetinára podľa jeho identifikátora."""
        user = UserRepo().get_user_by_id(florist_id)
        if user is None or not isinstance(user, Florista):
            raise ValueError("Invalid florist_id")
        return user
