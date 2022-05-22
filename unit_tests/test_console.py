import unittest

from modularizer.user_interface.user_interface import UserInterface
from modularizer.user_interface.console import Console


class MyTestCase(unittest.TestCase):
    def test_instantiation(self):
        self.assertIsInstance(Console(), UserInterface)


if __name__ == '__main__':
    unittest.main()
