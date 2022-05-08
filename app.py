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


class App:
    def __init__(self, database_connection: DatabaseConnection, projects_root: str = "home/katilippa/projects"):
        self.database_connection = database_connection
        self.multi_di_graph = nx.MultiDiGraph()
        self.graph = nx.Graph()
        self.communities = None
        self.projects_root = projects_root
        self.project_path = self.projects_root + "/" + database_connection.database
        self.build_dir = self.project_path + "/build"
        self.install_dir = self.project_path + "/install"
        self.set_variables()
        self.menu_options = [("Switch database", self.switch_database),
                             ("Display dependency graph", self.display_dependency_graph),
                             ("Display modules", self.display_modules),
                             ("Print modules", self.print_modules),
                             ("Save modules to file", self.save_modules_to_file)
                             ]

    def build_graph(self, dirs_to_exclude):
        self.database_connection.cursor.execute(
            'select distinct "CppEdge".from, \
                             fromFile.id as fromId, \
                             fromFile.path as fromPath, \
                             "CppEdge".to, \
                             toFile.id as toId, \
                             toFile.path as toPath, \
                             "CppEdge".type \
            from ("CppEdge" \
                 join ((select "File".path, \
                               "File".id, \
                               "CppEdge".to \
                        from "File" \
                             join "CppEdge" \
                                      on "CppEdge"."from" = "File".id) as fromFile \
            join (select "File".path, \
                         "File".id \
                  from "File" \
                        join "CppEdge" \
                                on "CppEdge"."to" = "File".id) as toFile \
                on fromFile."to" = toFile.id) \
                      on "CppEdge"."from" = fromFile.id and "CppEdge"."to" = toFile.id)')

        self.multi_di_graph = nx.MultiDiGraph()
        for record in self.database_connection.cursor.fetchall():
            if self.project_path in record[2] and all(path not in record[2] for path in dirs_to_exclude) and \
               self.project_path in record[5] and all(path not in record[5] for path in dirs_to_exclude):
                from_node = record[2].replace(self.projects_root, "").strip("/")
                to_node = record[5].replace(self.projects_root, "").strip("/")
                if not self.multi_di_graph.has_node(from_node):
                    self.multi_di_graph.add_node(from_node)
                if not self.multi_di_graph.has_node(to_node):
                    self.multi_di_graph.add_node(to_node)
                self.multi_di_graph.add_edges_from([(from_node, to_node)], label=EdgeType[record[6]])
        self.graph = self.multi_di_graph.to_undirected()

    def set_variables(self):
        # TODO ask for user input to specify paths to exlude
        self.project_path = self.projects_root + "/" + self.database_connection.database
        self.build_dir = self.project_path + "/build"
        if not os.path.exists("W:/" + self.build_dir):
            self.build_dir = self.project_path + "/Build"
        self.install_dir = self.project_path + "/install"
        self.build_graph(dirs_to_exclude=[self.build_dir, self.install_dir])
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

    def display_modules(self):
        pos = nx.spring_layout(self.graph)
        nx.draw(self.multi_di_graph, with_labels=True, pos=pos, font_size=8)
        colors = distinctipy.get_colors(len(self.communities))
        for i in range(len(self.communities)):
            nx.draw_networkx_nodes(self.graph, pos, nodelist=self.communities[i], node_color=colors[i])
        plt.show()

    def modules_to_json(self):
        modules = [[c for c in community] for community in self.communities]
        return json.dumps(list(modules), indent=4)

    def print_modules(self):
        print(self.modules_to_json())

    def save_modules_to_file(self):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results",
                                 f"{self.database_connection.database}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.modules_to_json())
