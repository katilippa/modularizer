import unittest
from modularizer.database_connection import DatabaseConnection


class MockDatabaseConnection(DatabaseConnection):
    def __init__(self):
        self.database = "DummyDatabase"
        self.user = "DummyUser"
        self.host = "DummyHost"
        self.port = "DummyPort"


class MyTestCase(unittest.TestCase):
    def test_to_string(self):
        expected_string = "database=DummyDatabase, user=DummyUser, host=DummyHost, port=DummyPort"
        db = MockDatabaseConnection()
        self.assertEqual(str(db), expected_string)  # add assertion here


if __name__ == '__main__':
    unittest.main()
