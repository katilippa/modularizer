from distinctipy import distinctipy
from getpass import getpass
from matplotlib import pyplot as plt
import networkx as nx
import pathlib
from tkinter import Tk
from typing import List, Tuple

from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from console import console_util
from console.console_menu import ConsoleMenu
from modularizer.user_interface.user_interface import UserInterface


class Console(UserInterface):
    _menu = None

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

    def display_dependency_graph(self, graph: nx.Graph) -> None:
        self._display_graph(graph)

    def display_all_modules(self, graph: nx.Graph, communities: list) -> None:
        colors = distinctipy.get_colors(len(communities))
        self._display_graph(graph, communities, colors)

    def display_module(self, graph: nx.Graph) -> None:
        self._display_graph(graph)

    def _display_graph(self, graph: nx.Graph, communities: list = None,
                       colors: List[Tuple[float, float, float]] = None) -> None:
        pos = nx.spring_layout(graph, seed=3)
        root = Tk()
        root.title('Modularizer')
        # root.iconphoto(False, 'info.png')
        try:
            root.state('zoomed')
        except Exception:
            root.attributes('-zoomed', True)
        # plt.switch_backend('TkAgg')
        fig = plt.figure()
        canvas = FigureCanvasTkAgg(fig, master=root)
        fig.set_tight_layout(True)

        node_min_size = 450
        multiplier = 50
        d = dict(graph.degree())
        if communities is None or colors is None:
            d = dict(graph.degree())
            nx.draw_networkx_nodes(graph, pos, node_size=[node_min_size+d[k]*multiplier for k in d])
        else:
            for i in range(len(communities)):
                nx.draw_networkx_nodes(graph, pos, nodelist=communities[i], node_color=[[c for c in colors[i]]],
                                       label=i,
                                       node_size=[node_min_size + d[k] * multiplier for k in d if k in communities[i]])
                lgnd = plt.legend()
                for handle in lgnd.legendHandles:
                    handle._sizes = [200]

        nx.draw_networkx_labels(graph, pos, font_size=7)

        straight_edges = []
        curved_edges = []
        edges = graph.edges()
        edge_labels = list(nx.get_edge_attributes(graph, 'label').items())
        curved_edge_labels = dict()
        straight_edge_labels = dict()
        i = 0
        for edge in edges:
            _, label = edge_labels[i]
            if graph.has_edge(edge[1], edge[0]):
                curved_edges.append(edge)
                curved_edge_labels[edge] = label
            else:
                straight_edges.append(edge)
                straight_edge_labels[edge] = label
            i += 1
        nx.draw_networkx_edges(graph, pos, edgelist=straight_edges, edge_color='grey', width=0.5)
        arc_rad = 0.25
        nx.draw_networkx_edges(graph, pos, edgelist=curved_edges,
                               connectionstyle=f'arc3, rad={arc_rad}', edge_color='grey', width=0.5)

        nx.draw_networkx_edge_labels(graph, pos, edge_labels=straight_edge_labels, rotate=False, font_size=6,
                                     font_color='grey')
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=curved_edge_labels, rotate=False, font_size=6,
                                     font_color='grey')

        toolbar = NavigationToolbar2Tk(canvas, root)
        toolbar.update()

        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()
