import logging
import unittest

from app import App
from database_connection import DatabaseConnection


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

    def test_collect_file_contents_for_module(self):
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

    def test_get_headers_and_source_files(self):
        files = self.app._collect_file_contents_for_module(1)
        headers, source_files = self.app._get_headers_and_source_files(files)
        print([str(h) for h in headers])
        print("---------------------------------------------------------------")
        print([str(s) for s in source_files])


if __name__ == '__main__':
    unittest.main()
