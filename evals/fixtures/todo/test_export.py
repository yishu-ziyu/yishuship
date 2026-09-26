import tempfile
import unittest
from pathlib import Path

import export
import todo


class ExportTest(unittest.TestCase):
    def test_markdown(self):
        with tempfile.TemporaryDirectory() as d:
            todo.DATA = Path(d) / "todos.json"
            todo.add("交房租")
            self.assertEqual(export.to_markdown(), "- [ ] 交房租\n")


if __name__ == "__main__":
    unittest.main()
