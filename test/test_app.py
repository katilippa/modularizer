import pathlib
import platform
import re
import unittest

from app import App, RegexPatterns
from database_connection import DatabaseConnection

# TODO: make tests independent from parsed projects

class MyTestCase(unittest.TestCase):
    app = App(database_connection=DatabaseConnection(database="CodeCompass", user='postgres', host='127.0.0.1',
                                                          port='5432'))

    def test_determinism(self):
        modules = []
        for i in range(10):
            app = App(database_connection=DatabaseConnection(database="CodeCompass", user='postgres', host='127.0.0.1',
                                                          port='5432'))
            modules.append(app.communities)
        i = 1
        while i < 10:
            self.assertEqual(modules[i-1], modules[i])
            self.assertEqual(len(modules[i]), len(modules[i-1]))
            print(f"i: {i-1}, len: {len(modules[i-1])}, len of first: {len(modules[i-1][0])}")
            i += 1

    def test_find_module_id_by_file_path(self):
        module_id = self.app._find_module_id_by_file_path("webserver/requesthandler.h")
        self.assertIsNotNone(module_id)
        self.assertGreaterEqual(module_id, 0)
        self.assertLess(module_id, len(self.app.communities))
        print(self.app.communities[module_id])

    def test_collect_files_for_module(self):
        module_id = self.app._find_module_id_by_file_path("webserver/requesthandler.h")
        print(module_id)
        print(self.app.communities[module_id])
        files = self.app._collect_file_contents_for_module(module_id)
        print([f.path for f in files])

    def test_query_file_contents(self):
        descriptor, results = self.app._query_file_contents(
            ["/home/katilippa/projects/CodeCompass/webserver/include/webserver/pluginhandler.h"])
        print(results)
        self.assertEqual(len(results), 1)  # add assertion here

    # def test_get_headers_and_source_files(self):
    #     files = self.app._collect_files_for_module(1)
    #     headers, source_files = self.app._get_headers_and_source_files(files)
    #     print([str(h) for h in headers])
    #     print("---------------------------------------------------------------")
    #     print([str(s) for s in source_files])

    def test_regex(self):
        file_path = (pathlib.PurePosixPath(__file__).parent).joinpath('data').joinpath("regex_test.txt")
        # descriptor, results = self.app._query_file_contents(
        #     ["/home/katilippa/projects/CodeCompass/webserver/include/webserver/mongoose.h"])
        # file_path = pathlib.PurePosixPath("W:").joinpath(results[0][self.app._find_column_index(descriptor, 'path')])
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        comments = re.findall(RegexPatterns.COMMENT.value, file_content, re.MULTILINE)
        for comment in comments:
            file_content = file_content.replace(comment, '')
        includes = re.findall(RegexPatterns.INCLUDE.value, file_content, re.MULTILINE)
        included_files = re.findall(RegexPatterns.INCLUDED_FILES.value, file_content, re.MULTILINE)
        self.assertEqual(len(includes), 4)
        self.assertEqual(len(comments), 5)
        #print(included_files)
        self.assertEqual(len(included_files), 4)

    def test_generate_module_file(self):
        module_id = self.app._find_module_id_by_file_path("webserver/requesthandler.h")
        self.app._generate_module_file(module_id, "webserver")

    def test_load_modules_from_file(self):
        self.app.load_modules_from_file(r'C:\Users\lippa\Google Drive\ELTE\Szakdolgozat\modularizer\results\CodeCompass_20220509_005153.json')
        self.assertGreater(len(self.app.communities), 0)

    def test_platform(self):
        print(platform.uname())
        print(platform.platform())

if __name__ == '__main__':
    unittest.main()
