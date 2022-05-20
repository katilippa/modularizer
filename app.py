import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import networkx as nx
from numpy import long
import os
import pathlib
import re
from typing import *

from database_connection import DatabaseConnection
from user_interface.user_interface import UserInterface


@dataclass
class File:
    id: long
    path: str
    filename: str
    content: str

    def __str__(self):
        return self.path


class RegexPatterns(Enum):
    COMMENT = r'^[^\S\n\r]*(?:\/\*(?:[^\*\/]*|(?:\/*|(?:\*[^\/])*))*(?:\*\/){1}|(?:(?:\/{2}.*)(?:\n|$)))'
    INCLUDE = r'((?:\n|\\n)*\s*#[^\S\n\r]*include[^\S\n\r]*(?:<[^>]+>|"[^"]+")(?:\n|\\n|$))'
    PREPROCESSING_DIRECTIVE = r'((?:\n|\\n)*\s*#[^\S\n\r]*(?:include|if|ifdef|ifndef|else|elif|elifdef|elifndef|endif|define|undef|error|pragma|line)[^\S\n\r]*[^\n\r]*(?:\n|\\n|$))'
    INCLUDED_FILES = r'(?:^#[^\S\n\r]*include[^\S\n\r]*)(<[^>]+>|"[^"]+")(?:\n|\\n|$)'


class App:
    _edge_type = {0: "Provides",
                  1: "Implements",
                  2: "Uses",
                  3: "Depends on"}

    results_dir = pathlib.Path(__file__).resolve().parent.joinpath('results')

    def __init__(self, ui: UserInterface, database_connection: DatabaseConnection = None):
        self.ui = ui
        if database_connection is None:
            self.database_connection = None
            try:
                file_path = pathlib.Path(__file__).resolve().parent.joinpath('data').joinpath(
                    'default_database_connection.json')
                with open(file_path, "r") as f:
                    database_connections = json.load(f)
            except Exception as ex:
                self.ui.info_msg(f'Could not load database connections: {str(ex)}')
            if database_connections is None:
                connection = self.ui.get_database_connection()
            else:
                connection = database_connections[0]
                if not ui.closed_question(f'default database connection:\n{connection}\nConnect to database?'):
                    connection = self.ui.get_database_connection()
            while True:
                try:
                    self._connect_to_database(connection)
                    break
                except Exception:
                    if self.ui.closed_question('Change connection?'):
                        connection = self.ui.get_database_connection()
                    else:
                        ui.info_msg('Closing the application...')
                        raise SystemExit()
        else:
            self.database_connection = database_connection

        self.multi_di_graph = nx.MultiDiGraph()
        self.graph = nx.Graph()
        self.communities = None
        self.modules = dict()
        self._set_default_values()
        self.menu_options = [("Switch database connection", self.switch_database_connection),
                             ("Display dependency graph", self.display_dependency_graph),
                             ("Display all modules", self.display_all_modules),
                             ("Display module", self.display_module),
                             ("Print modules", self.print_modules),
                             ("Save modules to file", self.save_modules_to_file),
                             ("Load modules from file", self.load_modules_from_file),
                             ("Reset default modules", self.reset_default_modules),
                             # ("Generate all module files", self.generate_module_files),
                             ("Generate module file", self.generate_module_file)
                             ]
        self.ui.load_menu_options(self.menu_options)

    def _connect_to_database(self, connection: dict):
        while True:
            try:
                self.database_connection = DatabaseConnection(connection)
                self.ui.info_msg("Successful database connection: " + str(self.database_connection))
                break
            except Exception as ex:
                if 'no password supplied' in str(ex):
                    connection['password'] = self.ui.get_password()
                else:
                    self.ui.info_msg(str(ex))
                    if not self.ui.closed_question('Retry?'):
                        raise ex

    def build_graph(self) -> None:
        query_file_path = pathlib.Path(__file__).resolve().parent.joinpath('data', 'cpp_edge_query.txt')
        with open(query_file_path, "r") as f:
            query = f.read()
        self.database_connection.cursor.execute(query)
        results = self.database_connection.cursor.fetchall()
        from_path_index = self._find_column_index(self.database_connection.cursor.description, 'frompath')
        to_path_index = self._find_column_index(self.database_connection.cursor.description, 'topath')
        project_name = self.database_connection.database
        project_root = ''
        for record in results:
            if project_name in record[from_path_index]:
                project_root = record[from_path_index]
                break
            elif project_name in record[to_path_index]:
                project_root = record[to_path_index]
                break

        if project_root == '':
            project_root = self.ui.get_user_input(
                f"Could not identify project root.\nEnter the parsed project's root directory")
        else:
            project_root = project_root[0:project_root.find(project_name) + len(project_name)]
            self.ui.info_msg(f'Projec root: {project_root}')

        build_dir_found = False
        for folder in ['build', 'Build']:
            build_dir = pathlib.PurePosixPath(project_root).joinpath(folder)
            i = 0
            while i < len(results) and not (str(build_dir) in str(pathlib.PurePosixPath(results[i][from_path_index]))) \
                    and not (str(build_dir) in str(pathlib.PurePosixPath(results[i][to_path_index]))):
                i += 1
            if i < len(results):
                build_dir_found = True
                break
        dirs_to_exclude = []
        if build_dir_found:
            self.ui.info_msg(f'Build directory found: {build_dir}\n It will be excluded from analysis.')
            dirs_to_exclude.append(build_dir)
        else:
            self.ui.info_msg(f'Build directory not found under project root.')
        while self.ui.closed_question('Do you want to exclude another directory?'):
            dir_to_exclude = self.ui.get_user_input("directory (relative to project root)")
            dirs_to_exclude.append(pathlib.PurePosixPath(project_root).joinpath(dir_to_exclude))

        self.multi_di_graph = nx.MultiDiGraph()
        for record in results:
            if project_root in record[from_path_index] and all(
                    str(path) not in record[to_path_index] for path in dirs_to_exclude) and \
                    project_root in record[to_path_index] and all(
                    str(path) not in record[from_path_index] for path in dirs_to_exclude):
                from_node = record[from_path_index].replace(project_root, "").strip("/")
                to_node = record[to_path_index].replace(project_root, "").strip("/")
                if not self.multi_di_graph.has_node(from_node):
                    self.multi_di_graph.add_node(from_node, path=record[from_path_index])
                if not self.multi_di_graph.has_node(to_node):
                    self.multi_di_graph.add_node(to_node, path=record[to_path_index])
                self.multi_di_graph.add_edges_from([(from_node, to_node)], label=self._edge_type[record[6]])
        self.graph = self.multi_di_graph.to_undirected()

    def _set_default_values(self) -> None:
        self.build_graph()
        self.graph = nx.Graph(self.graph)
        self.communities = nx.community.louvain_communities(self.graph, seed=3, resolution=1.1)
        self.modules = self._modules_to_dict()

    def switch_database_connection(self) -> None:
        while True:
            try:
                connection = self.ui.get_database_connection()
                self._connect_to_database(connection)
                break
            except Exception:
                if not self.ui.closed_question('Connect to other database?'):
                    self.ui.info_msg('Closing the application...')
                    raise SystemExit()
        self._set_default_values()

    def display_dependency_graph(self) -> None:
        self.ui.display_dependency_graph(self.multi_di_graph)

    def display_all_modules(self) -> None:
        self.ui.display_all_modules(self.multi_di_graph, self.communities)

    def display_module(self) -> None:
        module_id = self.ui.get_module_id(len(self.communities))
        community = self.multi_di_graph.subgraph(self.communities[module_id])
        self.ui.display_graph(community)

    def _modules_to_dict(self) -> Dict[int, List[str]]:
        modules = dict()
        for i in range(len(self.communities)):
            paths = [self.multi_di_graph.nodes[c]['path'] for c in self.communities[i]]
            modules[i] = paths
        return modules

    def _modules_to_json(self) -> str:
        return json.dumps(self.modules, indent=4)

    def print_modules(self) -> None:
        self.ui.info_msg(self._modules_to_json())

    def save_modules_to_file(self):
        os.makedirs(self.results_dir, exist_ok=True)
        file_path = os.path.join(self.results_dir,
                                 f'{self.database_connection.database}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self._modules_to_json())
        self.ui.info_msg(f'file saved: {file_path}')

    def _load_modules_from_file(self, file_path: str):
        with open(file_path, 'r') as f:
            modules = json.load(f)
        self.communities = []
        for module_id, files in modules.items():
            nodes = []
            for file in files:
                i = 0
                for node, data in self.multi_di_graph.nodes(data=True):
                    if data['path'] == file:
                        break
                    i += 1
                if i < len(self.multi_di_graph.nodes):
                    nodes.append(node)
                else:
                    raise Exception(f'Node not found for file: {file}')
            self.communities.append(self.graph.subgraph(nodes))
        self.modules = self._modules_to_dict()

    def load_modules_from_file(self):
        file_path = self.ui.get_existing_file_path()
        self._load_modules_from_file(file_path)
        self.ui.info_msg('Modules loaded')

    def reset_default_modules(self):
        self._set_default_values()

    def _query_file_contents(self, paths):
        query_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'file_content_query.txt')
        with open(query_file_path, 'r') as f:
            query = f.read().replace('<LIST_OF_PATHS>', ','.join([f"'{path}'" for path in paths]))
        self.database_connection.cursor.execute(query)
        results = self.database_connection.cursor.fetchall()
        return self.database_connection.cursor.description, results

    def _find_module_id_by_file_path(self, file_path: str):
        for i in range(len(self.communities)):
            for node in self.communities[i]:
                full_path = self.multi_di_graph.nodes[node]['path']
                if file_path in full_path:
                    return i
        return None

    @staticmethod
    def _find_column_index(description, column_name: str):
        i = 0
        for column in description:
            if column.name == column_name:
                return i
            else:
                i += 1

    @staticmethod
    def _get_topologically_sorted_nodes(graph):
        while not nx.is_directed_acyclic_graph(graph):
            cycle = nx.find_cycle(graph)
            new_graph = nx.MultiDiGraph(graph)
            new_graph.remove_edge(cycle[1][0], cycle[1][1])
            graph = new_graph
        return list(nx.topological_sort(graph))

    def _collect_file_contents_for_module(self, module_id: int) -> List[File]:
        community = self.multi_di_graph.subgraph(self.communities[module_id])
        sorted_nodes = self._get_topologically_sorted_nodes(community)
        sorted_nodes.reverse()
        paths = [self.multi_di_graph.nodes[n]['path'] for n in sorted_nodes]
        descriptor, results = self._query_file_contents(paths)
        path_index = self._find_column_index(descriptor, 'path')
        filename_index = self._find_column_index(descriptor, 'filename')
        content_index = self._find_column_index(descriptor, 'content')
        id_index = self._find_column_index(descriptor, 'id')
        files = [File(id=result[id_index], path=result[path_index], filename=result[filename_index],
                      content=result[content_index]) for result in results]
        sorted_files = []
        for path in paths:
            i = 0
            while files[i].path != path:
                i += 1
            if files[i].path == path:
                sorted_files.append(files[i])
            else:
                raise Exception(f'Content of file {path} not found in database')
        return sorted_files

    @staticmethod
    def _get_headers_and_source_files(files):
        headers = []
        source_files = []
        for file in files:
            if os.path.splitext(file.filename)[1].lower()[1] == "h":
                headers.append(file)
            else:
                source_files.append(file)
        return headers, source_files

    @staticmethod
    def _comment_out_unnecessary_includes(module_files: List[str], lines: List[str]):
        # included_files = re.findall(RegexPatterns.INCLUDED_FILES.value, file_content, re.MULTILINE)
        file_paths = []
        for path in module_files:
            file_paths.append(pathlib.PurePosixPath(path).parts)
        for line_index in range(len(lines)):
            line_start = lines[line_index][:len('#include <')]
            included_file = lines[line_index][len(line_start):len(lines[line_index]) - 1]
            if line_start == '#include <':
                if len(list(pathlib.PurePosixPath(included_file).parts)) > 1:
                    for path in module_files:
                        if included_file in path:
                            lines[line_index] = f'// {lines[line_index]}'
            elif line_start == '#include "':
                included_file_parts = list(pathlib.PurePosixPath(included_file).parts)
                for file_parts in file_paths:
                    i = 1
                    while i <= len(included_file_parts) and not file_parts[-i] == included_file_parts[-i]:
                        i += 1
                    if i <= len(included_file_parts) and file_parts[-i] == included_file_parts[-i]:
                        lines[line_index] = f'// {lines[line_index]}'
                        break
        return lines

    def _generate_module_file(self, module_id: int, module_name: str):
        files = self._collect_file_contents_for_module(module_id)
        headers, source_files = self._get_headers_and_source_files(files)
        files = headers + source_files
        global_module_fragment = ['module;', '\n']
        module_content = [f'export module {module_name};', '\n']
        for file in files:
            logging.debug(f'filename: {file.filename}')
            file_content = file.content
            comments = re.findall(RegexPatterns.COMMENT.value, file_content, re.RegexFlag.MULTILINE)
            logging.debug(f'removing {len(comments)} comment(s):\n{comments}')
            for comment in comments:
                file_content = file_content.replace(comment, '')
            preprocessing_directives = re.findall(RegexPatterns.PREPROCESSING_DIRECTIVE.value, file_content)
            global_module_fragment.append(f'// {file.filename}')
            pds_kept = []
            for pd in preprocessing_directives:
                file_content = file_content.replace(pd, '')
                include_guard_snippet = file.filename.replace('.', '_').upper()
                stripped_pd = pd.replace('\n', '').strip()
                if include_guard_snippet in pd.upper() or (
                        stripped_pd != '#endif' and stripped_pd != '#else' and (stripped_pd in global_module_fragment)):
                    pds_kept.append(f'// {stripped_pd}')
                elif '#endif' in pd or '#endif' == pd:
                    i = len(pds_kept) - 1
                    closed = 0
                    opened = 0
                    while i >= 0:

                        if '#endif' in pds_kept[i] or '#endif' == pds_kept[i] and not (pds_kept[i][:2] == '//'):
                            closed += 1
                        elif '#if' in pds_kept[i] or '#ifdef' in pds_kept[i] or '#ifndef' in pds_kept[i]:
                            if not (pds_kept[i][:2] == '//'):
                                opened += 1
                        i -= 1
                    if opened > closed:
                        pds_kept.append(stripped_pd)
                    else:
                        pds_kept.append(f'// {stripped_pd}')
                else:
                    pds_kept.append(stripped_pd)
            global_module_fragment = global_module_fragment + pds_kept
            global_module_fragment.append('\n')
            module_content.append(f'// {file.filename}')
            # TODO: decide if it is a header in a more sophisticated way
            if os.path.splitext(file.filename)[1].lower()[1] == 'h':
                file_content = file_content.replace('namespace', 'export namespace', 1)
                # TODO: export every symbols based on CppEntity
            module_content = module_content + file_content.splitlines()
            module_content.append('\n')
        global_module_fragment = self._comment_out_unnecessary_includes([file.path for file in files],
                                                                        global_module_fragment)
        global_module_fragment.append('\n')
        path = pathlib.PurePosixPath(self.results_dir).joinpath(self.database_connection.database)
        os.makedirs(path, exist_ok=True)
        full_path = path.joinpath(f'{module_name}.cpp')
        module = global_module_fragment + module_content
        module = '\n'.join(module)
        module = re.sub(r'\n{3,}', '\n\n', module, flags=re.RegexFlag.MULTILINE)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(module)
        self.ui.info_msg(f'Module file generated: {full_path}')

    def generate_module_files(self):
        for i in range(len(self.communities)):
            if len(self.modules[i]) > 0:
                module_name = self.ui.get_module_name(self.modules[i])
                self._generate_module_file(i, module_name)

    def generate_module_file(self):
        module_id = self.ui.get_module_id(len(self.communities))
        if len(self.modules[module_id]) > 0:
            module_name = self.ui.get_module_name(self.modules[module_id])
            self._generate_module_file(module_id, module_name)
        else:
            self.ui.info_msg('No file in module')
