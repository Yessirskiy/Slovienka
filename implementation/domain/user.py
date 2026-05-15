from abc import ABC


class User(ABC):
    def __init__(
        self, id: int, email: str, first_name: str, last_name: str, is_admin: bool
    ):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin


class Customer(User):
    def __init__(
        self, id: int, email: str, first_name: str, last_name: str, is_admin: bool
    ):
        super().__init__(id, email, first_name, last_name, is_admin)


class Florista(User):
    def __init__(
        self, id: int, email: str, first_name: str, last_name: str, is_admin: bool
    ):
        super().__init__(id, email, first_name, last_name, is_admin)


class Curier(User):
    def __init__(
        self, id: int, email: str, first_name: str, last_name: str, is_admin: bool
    ):
        super().__init__(id, email, first_name, last_name, is_admin)