import unittest
from typing import List, Tuple

import networkx as nx

from modularizer.user_interface.user_interface import UserInterface


class UIChildWithoutImplementations(UserInterface):
    pass


class UIChildWithImplementations(UserInterface):
    def get_password(self) -> str:
        pass

    def get_database_connection(self) -> dict:
        pass

    def info_msg(self, msg: str) -> None:
        pass

    def get_user_input(self, msg: str) -> str:
        pass

    def load_menu_options(self, menu_options: List[Tuple[str, callable]]) -> None:
        pass

    def closed_question(self, question: str) -> bool:
        pass

    def get_existing_directory_path(self, msg: str) -> str:
        pass

    def get_existing_file_path(self) -> str:
        pass

    def get_module_id(self, max_id: int) -> int:
        pass

    def get_module_name(self, module) -> str:
        pass

    def display_dependency_graph(self, graph: nx.Graph) -> None:
        pass

    def display_all_modules(self, graph: nx.Graph, communities: list) -> None:
        pass

    def display_module(self, graph: nx.Graph) -> None:
        pass


class UserInterfaceTest(unittest.TestCase):
    def test_instantiation(self):
        self.assertRaises(TypeError, UserInterface)

    def test_child_without_methods(self):
        self.assertRaises(TypeError, UIChildWithoutImplementations)

    def test_child_with_methods(self):
        self.assertIsInstance(UIChildWithImplementations(), UserInterface)


if __name__ == '__main__':
    unittest.main()
