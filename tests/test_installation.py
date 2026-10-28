import importlib
import pkgutil

import pytest

import ego

# scripts that are run from within ego/, not imported
SCRIPTS = {"ego.appl", "ego.run_test"}

MODULES = [
    module.name
    for module in pkgutil.walk_packages(ego.__path__, prefix="ego.")
    if module.name not in SCRIPTS
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    """All dependencies eGo imports are installed."""
    importlib.import_module(module)
