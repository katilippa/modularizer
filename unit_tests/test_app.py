import networkx as nx
import pandas
import pathlib
from psycopg2._psycopg import Column
import re
from typing import List, Tuple
import unittest

from modularizer.app import Modularizer
from modularizer.app import RegexPattern
from modularizer.user_interface.console import Console
from modularizer.database_connection import DatabaseConnection
from modularizer.user_interface.user_interface import UserInterface

# class MockUserInterface(Console):
#     def load_menu_options(self, menu_options: List[Tuple[str, callable]]) -> None:
#         pass
#
#     def closed_question(self, question: str) -> bool:
#         if 'Connect to database?' in question:
#             return True
#         else:
#             return False
#
#
# class MockDatabaseConnection(DatabaseConnection):
#     class cursor:
#         description = None
#         data = None
#
#         def fetchall(self):
#             pass
#
#         def execute(self, query: str):
#             pass
#
#     def __init__(self):
#         self.database = "DummyDatabase"
#         self.user = "DummyUser"
#         self.host = "DummyHost"
#         self.port = "DummyPort"
cpp_edge_results_description = (
    Column(name='from', type_code=20), Column(name='fromid', type_code=20), Column(name='frompath', type_code=25),
    Column(name='to', type_code=20), Column(name='toid', type_code=20), Column(name='topath', type_code=25),
    Column(name='type', type_code=23))

file_contents_description = (
    Column(name='id', type_code=20), Column(name='path', type_code=25), Column(name='filename', type_code=25),
    Column(name='content', type_code=25))


class ModularizerTest(unittest.TestCase):

    def setUp(self) -> None:
        dummy_cpp_edge_results_file = pathlib.Path(__file__).resolve().parent.joinpath('data').joinpath(
            'dummy_cpp_edge_results.csv')
        self.dummy_cpp_edge_results = pandas.read_csv(dummy_cpp_edge_results_file).values

        dummy_file_content_results_file = pathlib.Path(__file__).resolve().parent.joinpath('data').joinpath(
            'dummy_file_content_results.csv')
        self.dummy_file_content_results_file = pandas.read_csv(dummy_file_content_results_file).values
        self.dummy_file_content_results = ""

    @staticmethod
    def get_indexes():
        from_path_index = Modularizer.find_column_index(cpp_edge_results_description, 'frompath')
        to_path_index = Modularizer.find_column_index(cpp_edge_results_description, 'topath')
        return from_path_index, to_path_index

    def test_find_column_index(self):
        description1 = (Column(name='frompath', type_code=25), Column(name='topath', type_code=25),
                        Column(name='type', type_code=23))
        index = Modularizer.find_column_index(description1, 'frompath')
        self.assertEqual(index, 0)
        index = Modularizer.find_column_index(description1, 'topath')
        self.assertEqual(index, 1)
        index = Modularizer.find_column_index(description1, 'type')
        self.assertEqual(index, 2)

    def test_find_non_existent_column(self):
        with self.assertRaises(Exception):
            Modularizer.find_column_index(cpp_edge_results_description, 'does_not_exist')

    def test_find_project_root(self):
        from_path_index, to_path_index = self.get_indexes()
        project_root = Modularizer.find_project_root('CodeCompass', self.dummy_cpp_edge_results, from_path_index,
                                                     to_path_index)
        self.assertEqual(project_root, '/home/katilippa/projects/test/CodeCompass')
        project_root = Modularizer.find_project_root('asd', self.dummy_cpp_edge_results, from_path_index,
                                                     to_path_index)
        self.assertEqual(project_root, '')
        results = [["", "", "", "", "", ""]]
        project_root = Modularizer.find_project_root('CodeCompass', results, from_path_index,
                                                     to_path_index)
        self.assertEqual(project_root, '')

    def test_find_build_dir(self):
        from_path_index, to_path_index = self.get_indexes()
        project_root = Modularizer.find_project_root('CodeCompass', self.dummy_cpp_edge_results, from_path_index,
                                                     to_path_index)
        build_dir = Modularizer.find_build_dir(self.dummy_cpp_edge_results, project_root, from_path_index,
                                               to_path_index)
        self.assertEqual(build_dir, '/home/katilippa/projects/test/CodeCompass/Build')
        results = [["", "", "", "", "", ""]]
        build_dir = Modularizer.find_build_dir(results, project_root, from_path_index, to_path_index)
        self.assertEqual(build_dir, '')

    def get_graph_from_dummy_data(self):
        from_path_index, to_path_index = self.get_indexes()
        project_root = Modularizer.find_project_root('CodeCompass', self.dummy_cpp_edge_results, from_path_index,
                                                     to_path_index)
        build_dir = Modularizer.find_build_dir(self.dummy_cpp_edge_results, project_root, from_path_index,
                                               to_path_index)
        return Modularizer.graph_from_query_results(self.dummy_cpp_edge_results, project_root, [build_dir],
                                                    from_path_index, to_path_index)

    def test_build_graph(self):
        graph = self.get_graph_from_dummy_data()
        self.assertEqual(len(graph.nodes), 156)
        self.assertEqual(len(graph.edges), 368)

    def test_get_communities(self):
        communities = Modularizer.get_communities(self.get_graph_from_dummy_data())
        self.assertEqual(len(communities), 10)

    def test_load_modules_from_file(self):
        graph = self.get_graph_from_dummy_data()
        test_modules_file = pathlib.Path(__file__).resolve().parent.joinpath('data').joinpath(
            'test_modules.json')
        modules = Modularizer.load_modules_from_file(test_modules_file, graph)
        self.assertEqual(len(modules), 3)
        self.assertEqual(len(modules[0]), 9)
        self.assertEqual(len(modules[1]), 2)
        self.assertEqual(len(modules[2]), 11)

    def test_load_modules_from_invalid_file(self):
        graph = self.get_graph_from_dummy_data()
        test_modules_invalid_file = pathlib.Path(__file__).resolve().parent.joinpath('data').joinpath(
            'test_modules_invalid.json')
        with self.assertRaises(Exception):
            modules = Modularizer.load_modules_from_file(test_modules_invalid_file, graph)

    def get_test_modules(self):
        graph = self.get_graph_from_dummy_data()
        test_modules_file = pathlib.Path(__file__).resolve().parent.joinpath('data').joinpath(
            'test_modules.json')
        return Modularizer.load_modules_from_file(test_modules_file, graph)

    def test_convert_graph_to_dag(self):
        graph = self.get_test_modules()[2]
        self.assertFalse(nx.is_directed_acyclic_graph(graph))
        graph = Modularizer.convert_graph_to_dag(graph)
        self.assertTrue(nx.is_directed_acyclic_graph(graph))

    def test_get_topologically_sorted_nodes(self):
        graph = self.get_test_modules()[1]
        expected_sorted_nodes = ['service/workspace/src/workspaceservice.cpp',
                                 'service/workspace/include/workspaceservice/workspaceservice.h']
        sorted_nodes = Modularizer.get_topologically_sorted_nodes(graph)
        self.assertSequenceEqual(expected_sorted_nodes, sorted_nodes)

    def test_regex_comments(self):
        file_path = pathlib.Path(__file__).resolve().parent.joinpath('data').joinpath("regex_test.txt")
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        comments = re.findall(RegexPattern.COMMENT.value, file_content, re.MULTILINE)
        self.assertEqual(len(comments), 5)
        expected_comments = ['//#include <algorithm>\n', '/* #include <map> */', '// ...\n',
                             '/********\n block comment\n*********/', '// eof']
        self.assertSequenceEqual(expected_comments, comments)

    def test_regex_preprocessing_directives(self):
        file_path = pathlib.Path(__file__).resolve().parent.joinpath('data').joinpath("regex_test.txt")
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        pds = re.findall(RegexPattern.PREPROCESSING_DIRECTIVE.value, file_content, re.MULTILINE)
        self.assertEqual(len(pds), 9)
        expected_pds = ['#ifndef FOO_H\n', '#define FOO_H\n', '#include <iostream>\n', '#include <memory>\n',
                        '#include <string>\n', '#include <vector>\n', '\n#include "bar.h"\n',
                        '\n\n#define PI   3.14159\n', '\n#endif\n']
        self.assertSequenceEqual(expected_pds, pds)

    def test_comment_out_include_guards(self):
        pds = ['#ifndef CC_SERVICE_WORKSPACE_WORKSPACESERVICE_H\n', '#define CC_SERVICE_WORKSPACE_WORKSPACESERVICE_H\n',
               '#ifndef something', '#define something', '#endif', '\n#include <WorkspaceService.h>\n',
               '\n#endif // CC_SERVICE_WORKSPACE_WORKSPACESERVICE_H\n']
        result = Modularizer.comment_out_include_guards('workspaceservice.h', pds)
        expected_result = ['// #ifndef CC_SERVICE_WORKSPACE_WORKSPACESERVICE_H',
                           '// #define CC_SERVICE_WORKSPACE_WORKSPACESERVICE_H',
                           '#ifndef something', '#define something', '#endif', '#include <WorkspaceService.h>',
                           '// #endif // CC_SERVICE_WORKSPACE_WORKSPACESERVICE_H']
        self.assertSequenceEqual(expected_result, result)

    def test_comment_out_unnecessary_includes(self):
        pds = ['#include <memory>', '\n#include <workspaceservice/workspaceservice.h>\n', '\n#include <iostream>']
        module_files = ['CodeCompass/service/workspace/include/workspaceservice/workspaceservice.h',
                        'CodeCompass/service/workspace/src/workspaceservice.cpp']
        result = Modularizer.comment_out_unnecessary_includes(module_files, pds)
        expected_result = ['#include <memory>', '// #include <workspaceservice/workspaceservice.h>', '#include <iostream>']
        self.assertSequenceEqual(expected_result, result)

    def test_comment_out_duplicate_includes(self):
        global_module_fragment = ['#include <iostream>',
                                  '#ifndef something', '#define something', '#endif', '#include <WorkspaceService.h>',
                                  '#ifndef something_else', '#define something_else', '#endif',
                                  '#include <WorkspaceService.h>', '#include <vector>']
        pds = ['#include <memory>', '\n#include <workspaceservice.h>\n', '\n#include <iostream>']
        result = Modularizer.comment_out_duplicate_includes(global_module_fragment, pds)
        expected_result = ['#include <memory>', '\n#include <workspaceservice.h>\n', '// #include <iostream>']
        self.assertSequenceEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
