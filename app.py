from distinctipy import distinctipy
from datetime import datetime
import json
import matplotlib.pyplot as plt
import networkx as nx
import os

from database_connection import DatabaseConnection

EdgeType = {0: "Provides",
            1: "Implements",
            2: "Uses",
            3: "Depends on"}


def find_column_index(description, column_name: str):
    i = 0
    for column in description:
        if column.name == column_name:
            return i
        else:
            i += 1


class App:
    def __init__(self, database_connection: DatabaseConnection):
        self.database_connection = database_connection
        self.multi_di_graph = nx.MultiDiGraph()
        self.graph = nx.Graph()
        self.communities = None
        self.project_path = ""
        self.build_dir = ""
        self.install_dir = ""
        self.set_variables()
        self.menu_options = [("Switch database", self.switch_database),
                             ("Display dependency graph", self.display_dependency_graph),
                             ("Display all modules", self.display_all_modules),
                             ("Display module", self.display_module),
                             ("Print modules", self.print_modules),
                             ("Save modules to file", self.save_modules_to_file)
                             ]

    def build_graph(self):
        with open("data/cpp_edge_query.txt", "r") as f:
            query = f.read()
        self.database_connection.cursor.execute(query)
        results = self.database_connection.cursor.fetchall()
        from_path_index = find_column_index(self.database_connection.cursor.description, "frompath")
        to_path_index = find_column_index(self.database_connection.cursor.description, "topath")

        project_name = self.database_connection.database
        path = ""
        for record in results:
            if project_name in record[from_path_index]:
                path = record[from_path_index]
                break
            elif project_name in record[to_path_index]:
                path = record[to_path_index]
                break
        # TODO: if project folder not found, ask for user input

        self.project_path = path[0:path.find(project_name) + len(project_name)]
        self.build_dir = self.project_path + "/build"
        if not os.path.exists("W:/" + self.build_dir):
            self.build_dir = self.project_path + "/Build"
        self.install_dir = self.project_path + "/install"
        dirs_to_exclude = [self.build_dir, self.install_dir]
        self.multi_di_graph = nx.MultiDiGraph()
        for record in results:
            if self.project_path in record[from_path_index] and all(
               path not in record[to_path_index] for path in dirs_to_exclude) and \
               self.project_path in record[to_path_index] and all(
               path not in record[from_path_index] for path in dirs_to_exclude):
                from_node = record[from_path_index].replace(self.project_path, "").strip("/")
                to_node = record[to_path_index].replace(self.project_path, "").strip("/")
                if not self.multi_di_graph.has_node(from_node):
                    self.multi_di_graph.add_node(from_node)
                if not self.multi_di_graph.has_node(to_node):
                    self.multi_di_graph.add_node(to_node)
                self.multi_di_graph.add_edges_from([(from_node, to_node)], label=EdgeType[record[6]])
        self.graph = self.multi_di_graph.to_undirected()

    def set_variables(self):
        # TODO ask for user input to specify paths to exclude
        self.build_graph()
        self.graph = nx.Graph(self.graph)
        self.communities = nx.community.louvain_communities(self.graph)

    def switch_database(self):
        database = input("database: ")
        self.database_connection = DatabaseConnection(database=database)
        self.set_variables()

    def display_dependency_graph(self):
        pos = nx.spring_layout(self.graph)
        nx.draw(self.multi_di_graph, with_labels=True, pos=pos, font_size=8)
        # edge_labels = nx.get_edge_attributes(self.di_graph, 'label')
        # nx.draw_networkx_edge_labels(self.graph, edge_labels=edge_labels, pos=pos)
        plt.show()

    def display_all_modules(self):
        pos = nx.spring_layout(self.graph)
        nx.draw(self.multi_di_graph, with_labels=True, pos=pos, font_size=8)
        colors = distinctipy.get_colors(len(self.communities))
        for i in range(len(self.communities)):
            nx.draw_networkx_nodes(self.graph, pos, nodelist=self.communities[i], node_color=[[c for c in colors[i]]],
                                   label=i)
        plt.legend()
        plt.show()

    def display_module(self):
        str_id = input("module id: ")
        while not (str_id.isdigit() and 0 <= int(str_id) < len(self.communities)):
            print("invalid module id")
            str_id = input("module id: ")
        community = self.multi_di_graph.subgraph(self.communities[int(str_id)])
        pos = nx.spring_layout(community)
        nx.draw(community, with_labels=True, pos=pos, font_size=8)
        plt.show()

    def modules_to_json(self):
        modules = dict()
        for i in range(len(self.communities)):
            list = [c for c in self.communities[i]]
            modules[i] = list
        return json.dumps(modules, indent=4)

    def print_modules(self):
        print(self.modules_to_json())

    def save_modules_to_file(self):
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        os.makedirs(results_dir, exist_ok=True)
        file_path = os.path.join(results_dir,
                                 f"{self.database_connection.database}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.modules_to_json())
