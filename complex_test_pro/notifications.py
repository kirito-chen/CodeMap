"""Notification services using class methods and static methods."""

class EmailNotifier:
    """Handles email notifications."""

    @classmethod
    def send_order_confirmation(cls, email: str, order_id: int):
        cls._send_email(email, f"Order {order_id} confirmed")

    @staticmethod
    def _send_email(to: str, message: str):
        print(f"Sending email to {to}: {message}")


class SMSNotifier:
    """Handles SMS notifications."""

    def send_sms(self, phone: str, text: str):
        print(f"Sending SMS to {phone}: {text}")


class NotificationService:
    """Facade for sending notifications."""

    def __init__(self):
        self.sms_sender = SMSNotifier()

    def notify(self, user_email: str, user_phone: str, order_id: int):
        EmailNotifier.send_order_confirmation(user_email, order_id)
        self.sms_sender.send_sms(user_phone, f"Order {order_id} placed")