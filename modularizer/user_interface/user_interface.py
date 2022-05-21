from abc import abstractmethod
import networkx as nx
from typing import List, Tuple


class UserInterface:
    def __init__(self) -> None:
        pass

    def __new__(cls):
        if cls is UserInterface:
            raise TypeError(f"only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    @abstractmethod
    def get_if_get_database_connection_ok(self):
        pass

    @abstractmethod
    def select_database_connection(self):
        pass

    @abstractmethod
    def get_password(self) -> str:
        pass

    @abstractmethod
    def get_database_connection(self) -> dict:
        pass

    @abstractmethod
    def info_msg(self, msg: str) -> None:
        pass

    @abstractmethod
    def get_user_input(self, msg: str) -> str:
        pass

    @abstractmethod
    def load_menu_options(self, menu_options: List[Tuple[str, callable]]) -> None:
        pass

    @abstractmethod
    def closed_question(self, question: str) -> bool:
        pass

    @abstractmethod
    def get_existing_directory_path(self, msg: str) -> str:
        pass

    @abstractmethod
    def get_existing_file_path(self) -> str:
        pass

    @abstractmethod
    def get_module_id(self, max_id: int) -> int:
        pass

    @abstractmethod
    def get_module_name(self, module) -> str:
        pass

    @abstractmethod
    def display_dependency_graph(self, graph: nx.Graph) -> None:
        pass

    @abstractmethod
    def display_all_modules(self, graph: nx.Graph, communities: list) -> None:
        pass

    @abstractmethod
    def display_module(self, graph: nx.Graph) -> None:
        pass
