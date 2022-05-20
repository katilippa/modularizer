from distinctipy import distinctipy
from getpass import getpass
from matplotlib import pyplot as plt
import networkx as nx
import pathlib
from typing import List, Tuple

from console import console_util
from console.console_menu import ConsoleMenu
from modularizer.user_interface.user_interface import UserInterface


class Console(UserInterface):
    _menu = None
    _pos = None

    def get_if_get_database_connection_ok(self):
        pass

    def select_database_connection(self):
        pass

    def get_password(self) -> str:
        return getpass('password: ')

    def get_database_connection(self) -> dict:
        connection = dict()
        connection['database'] = input('database: ')
        connection['user'] = input('user: ')
        connection['host'] = input('host: ')
        connection['port'] = input('port: ')
        return connection

    def info_msg(self, msg: str) -> None:
        print(msg)

    def get_user_input(self, msg: str) -> str:
        return input(f'{msg}: ')

    def closed_question(self, question: str) -> bool:
        return console_util.closed_question(question)

    def load_menu_options(self, menu_options: List[Tuple[str, callable]]) -> None:
        self._menu = ConsoleMenu(menu_options, 'Options')

    def get_existing_directory_path(self, msg: str) -> str:
        while True:
            path = input(f'{msg}: ')
            if not pathlib.Path(path).exists():
                print('Directory not found')
            else:
                return path

    def get_existing_file_path(self) -> str:
        file_path = input('file path: ')
        if pathlib.Path(file_path).exists():
            return file_path
        else:
            raise Exception('File not found')

    def get_module_id(self, max_id: int) -> int:
        str_id = self.get_user_input('module id')
        if str_id.isdigit() and 0 <= int(str_id) < max_id:
            return int(str_id)
        else:
            raise Exception('Invalid module id')

    def get_module_name(self, module) -> str:
        self.info_msg(f'Please name the following module: \n{module}\n')
        while True:
            module_name = self.get_user_input('module name')
            if module_name.replace('.', '').replace(':', '').isidentifier():
                return module_name
            else:
                if not self.closed_question(f'invalid module name\nTry again?'):
                    raise Exception('Operation aborted')

    def display_dependency_graph(self, multi_di_graph: nx.MultiDiGraph) -> None:
        self._set_pos(nx.Graph(multi_di_graph))
        # plt.figure(figsize=(16, 10))
        plt.switch_backend('TkAgg')
        mng = plt.get_current_fig_manager()
        ### works on Ubuntu??? >> did NOT working on windows
        # mng.resize(*mng.window.maxsize())
        mng.window.state('zoomed')
        nx.draw(multi_di_graph, with_labels=True, pos=self._pos, font_size=8)
        # edge_labels = nx.get_edge_attributes(self.di_graph, 'label')
        # nx.draw_networkx_edge_labels(self.graph, edge_labels=edge_labels, pos=pos)

        plt.show()

    def display_all_modules(self, multi_di_graph: nx.MultiDiGraph, communities: list) -> None:
        graph = nx.Graph(multi_di_graph)
        self._set_pos(graph)
        nx.draw(multi_di_graph, with_labels=True, pos=self._pos, font_size=8)
        colors = distinctipy.get_colors(len(communities))
        for i in range(len(communities)):
            nx.draw_networkx_nodes(graph, self._pos, nodelist=communities[i], node_color=[[c for c in colors[i]]],
                                   label=i)
        plt.legend()
        plt.show()

    def display_module(self, graph: nx.Graph) -> None:
        pos = nx.spring_layout(nx.Graph(graph), seed=1)
        nx.draw(graph, with_labels=True, pos=pos, font_size=8)
        plt.show()

    def _set_pos(self, graph: nx.Graph) -> None:
        if self._pos is None:
            self._pos = nx.spring_layout(graph, seed=3)