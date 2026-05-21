"""Entry point: create objects and run order processing."""

from .database import DBConnection
from .order_processor import OrderProcessor, OrderFactory

def main():
    # Setup
    db = DBConnection("sqlite:///test.db")
    db.connect()

    processor = OrderProcessor(db)
    sample_order = OrderFactory.create_sample_order()

    # Process order with different payment methods
    processor.process_order(sample_order, "credit")
    processor.process_order(sample_order, "paypal")

    db.disconnect()

if __name__ == "__main__":
    main()