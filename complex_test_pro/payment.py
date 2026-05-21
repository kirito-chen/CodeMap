"""Payment handling with abstract base class and implementations."""

from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    """Abstract payment processor."""

    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass

    @staticmethod
    def get_gateway(type_name: str) -> "PaymentGateway":
        if type_name == "credit":
            return CreditCardPayment()
        elif type_name == "paypal":
            return PayPalPayment()
        else:
            raise ValueError("Unknown gateway")


class CreditCardPayment(PaymentGateway):
    def pay(self, amount: float) -> bool:
        print(f"Processing credit card payment of ${amount}")
        return True


class PayPalPayment(PaymentGateway):
    def pay(self, amount: float) -> bool:
        print(f"Processing PayPal payment of ${amount}")
        return True


def process_payment(amount: float, method: str) -> bool:
    """Helper function to process payment."""
    gateway = PaymentGateway.get_gateway(method)
    return gateway.pay(amount)