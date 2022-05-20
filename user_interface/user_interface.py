from typing import List, Tuple

import networkx as nx


class UserInterface:
    def __init__(self) -> None:
        pass

    def __new__(cls):
        if cls is UserInterface:
            raise TypeError(f"only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def get_if_get_database_connection_ok(self):
        pass

    def select_database_connection(self):
        pass

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

    def display_dependency_graph(self, multi_di_graph: nx.MultiDiGraph) -> None:
        pass

    def display_all_modules(self, multi_di_graph: nx.MultiDiGraph, communities: list) -> None:
        pass

    def display_graph(self, graph: nx.Graph) -> None:
        pass
