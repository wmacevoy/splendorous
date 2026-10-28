"""The dependency rule from DESIGN_v1, checked mechanically (SE1/D10): a module imports only from
modules in strictly lower layers. Without this check, the layering is decoration."""
import ast
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "splendorous"
LAYERS = {"guide": 0, "cards": 1, "engine": 2, "bots": 3, "cli": 4, "__main__": 5, "__init__": 5}


def imports_of(path: Path):
    tree = ast.parse(path.read_text(encoding="utf8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            yield node.module
        if isinstance(node, ast.ImportFrom) and node.level == 1 and not node.module:
            for alias in node.names:
                yield alias.name
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module and node.module.startswith("splendorous."):
            yield node.module.split(".", 1)[1]
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("splendorous."):
                    yield alias.name.split(".", 1)[1]


class TestDependencyRule(unittest.TestCase):
    def test_every_module_is_in_a_layer_and_imports_only_lower_ones(self):
        """Chore: the layer table in DESIGN_v1 is enforced, not described."""
        modules = {p.stem: p for p in PACKAGE.glob("*.py")}
        self.assertEqual(set(modules), set(LAYERS), "a new module needs a layer in DESIGN_v1 and here")
        for name, path in modules.items():
            for imported in imports_of(path):
                self.assertIn(imported, LAYERS, f"{name} imports unknown module {imported}")
                self.assertLess(LAYERS[imported], LAYERS[name], f"{name} (layer {LAYERS[name]}) imports {imported} (layer {LAYERS[imported]})")


if __name__ == "__main__":
    unittest.main()
