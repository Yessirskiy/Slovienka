from domain.user import User, Customer, Florista


class UserRepo:
    def __init__(self):
        self.users = {
            0: Customer(0, "robert@slovienka.sk", "Róbert", "Tóth", False),
            1: Customer(1, "nikolai@slovienka.sk", "Nikolai", "Dobrydnev", False),
            2: Florista(2, "milan@slovienka.py", "Milan", "Šeliga", False),
        }

    def get_user_by_id(self, id: int) -> User | None:
        return self.users.get(id, None)