"""Core order processing logic with multiple call types."""

from typing import Optional
from .models import Order, Product, User
from .database import DBConnection, UserRepository
from .payment import process_payment
from .notifications import NotificationService

class DiscountCalculator:
    """Calculates discounts based on order value and user type."""

    def calculate(self, order: Order, user: User) -> float:
        total = order.total_amount()
        if total > 100:
            return total * 0.1  # 10% discount
        return 0.0

    @staticmethod
    def is_eligible_for_free_shipping(order: Order) -> bool:
        return order.total_amount() > 50


class OrderProcessor:
    """Main class to process orders."""

    def __init__(self, db_conn: DBConnection):
        self.db = db_conn
        self.user_repo = UserRepository(db_conn)
        self.notifier = NotificationService()
        self.discount_calc = DiscountCalculator()

    def process_order(self, order: Order, payment_method: str) -> bool:
        """Process an order: validate, apply discount, charge, notify."""
        # Ensure user exists (mock)
        user = self.user_repo.find_by_id(order.user.id)
        if not user:
            return False

        # Calculate discount
        discount = self.discount_calc.calculate(order, user)
        final_amount = order.total_amount() - discount

        # Process payment
        success = self._charge_payment(final_amount, payment_method)
        if not success:
            return False

        # Send notifications
        self._send_order_notifications(order, user)

        return True

    def _charge_payment(self, amount: float, method: str) -> bool:
        """Internal helper for payment."""
        return process_payment(amount, method)

    def _send_order_notifications(self, order: Order, user: User):
        """Internal helper for notifications."""
        self.notifier.notify(user.email, "1234567890", order.id)


class OrderFactory:
    """Factory to create test orders."""

    @staticmethod
    def create_sample_order() -> Order:
        user = User(1, "Alice", "alice@example.com")
        order = Order(1001, user)
        product1 = Product(101, "Laptop", 999.99)
        product2 = Product(102, "Mouse", 25.50)
        order.add_item(product1, 1)
        order.add_item(product2, 2)
        return order