"""Database simulation with classes and query builder."""

from typing import List, Dict, Any
from .models import User, Product, Order

class DBConnection:
    """Simulates a database connection."""

    def __init__(self, connection_string: str):
        self.conn_str = connection_string
        self._connected = False

    def connect(self):
        self._connected = True
        print(f"Connected to {self.conn_str}")

    def disconnect(self):
        self._connected = False
        print("Disconnected")

    def execute(self, query: str) -> List[Dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("Not connected")
        # Mock execution
        return [{"mock": "data"}]


class QueryBuilder:
    """Helper to build SQL queries."""

    @staticmethod
    def select(table: str, columns: List[str]) -> str:
        cols = ", ".join(columns)
        return f"SELECT {cols} FROM {table}"

    @classmethod
    def select_all(cls, table: str) -> str:
        return cls.select(table, ["*"])

    def where(self, condition: str) -> str:
        # This is not a real builder, just for demo
        return f"WHERE {condition}"


class UserRepository:
    """Repository for User operations."""

    def __init__(self, db: DBConnection):
        self.db = db

    def find_by_id(self, user_id: int) -> User:
        query = QueryBuilder.select_all("users")
        self.db.execute(query)
        # Mock: return a dummy user
        return User(user_id, "John Doe", "john@example.com")