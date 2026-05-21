"""Data models for the e-commerce system."""

class User:
    """Represents a customer."""

    def __init__(self, user_id: int, name: str, email: str):
        self.id = user_id
        self.name = name
        self.email = email

    def get_display_name(self) -> str:
        return f"{self.name} <{self.email}>"

    @staticmethod
    def from_dict(data: dict) -> "User":
        return User(data["id"], data["name"], data["email"])


class Product:
    """Represents a purchasable item."""

    def __init__(self, product_id: int, name: str, price: float):
        self.id = product_id
        self.name = name
        self.price = price

    def apply_discount(self, percent: float) -> float:
        return self.price * (1 - percent / 100)


class Order:
    """Represents an order with line items."""

    def __init__(self, order_id: int, user: User):
        self.id = order_id
        self.user = user
        self.items = []  # list of (product, quantity)

    def add_item(self, product: Product, quantity: int):
        self.items.append((product, quantity))

    def total_amount(self) -> float:
        total = 0.0
        for product, qty in self.items:
            total += product.price * qty
        return total

    def get_item_count(self) -> int:
        return sum(qty for _, qty in self.items)