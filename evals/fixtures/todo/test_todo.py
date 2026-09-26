import json
import tempfile
import unittest
from pathlib import Path

import todo


class TodoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        todo.DATA = Path(self.tmp.name) / "todos.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_done(self):
        todo.add("买牛奶", "2026-10-01")
        todo.done(1)
        self.assertEqual(json.loads(todo.DATA.read_text())[0]["done"], True)

    def test_rejects_bad_date(self):
        with self.assertRaises(ValueError):
            todo.add("x", "2026-13-01")


if __name__ == "__main__":
    unittest.main()
