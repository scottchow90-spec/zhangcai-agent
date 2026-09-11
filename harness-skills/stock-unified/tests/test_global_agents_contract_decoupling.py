# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json
import os
import ast
from pathlib import Path


HOME = Path(r"D:\C盘转移\日志\codex")
GLOBAL_AGENTS_PATH = HOME / "AGENTS.md"
CONTRACTS_PATH = (
    HOME
    / "skills"
    / "stock-unified"
    / "references"
    / "stock_execution_contracts.json"
)


def _same_file(left: Path, right: Path) -> bool:
    try:
        return os.path.samefile(left, right)
    except (FileNotFoundError, OSError):
        return left.resolve(strict=False) == right.resolve(strict=False)


def _business_bindings(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "business_bindings" and isinstance(child, list):
                yield from child
            yield from _business_bindings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _business_bindings(child)


def test_global_agents_is_not_sha_bound_into_each_stock_contract():
    catalog = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
    bound_paths = []
    for binding in _business_bindings(catalog):
        if not isinstance(binding, dict) or not binding.get("path"):
            continue
        path = Path(binding["path"])
        if _same_file(path, GLOBAL_AGENTS_PATH):
            bound_paths.append(str(path))

    assert not bound_paths, (
        "The mutable global AGENTS.md must not be copied into every stock "
        f"contract as a SHA binding: {bound_paths}"
    )


def test_global_agents_still_declares_canonical_stock_rule_semantics():
    rules = GLOBAL_AGENTS_PATH.read_text(encoding="utf-8")
    required_markers = (
        "stock_skill_ids.json",
        "stock_execution_contracts.json",
        "stock_canonical_runtime.py",
        "codex_entry.py run",
        "authorize --receipt",
    )
    missing = [marker for marker in required_markers if marker not in rules]
    assert not missing, f"Global stock execution rules are missing: {missing}"


def test_catalog_source_has_no_mutable_global_agents_binding_symbol():
    source_path = (
        HOME
        / "skills"
        / "stock-unified"
        / "scripts"
        / "stock_contract_catalog.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    uses = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "GLOBAL_AGENTS_PATH":
            uses.append((node.lineno, lines[node.lineno - 1].strip()))
    assert not uses, (
        "The catalog must validate global rules separately, not expose the "
        f"mutable file as a binding symbol. Remaining uses: {uses}"
    )


def test_catalog_normalization_explicitly_filters_historical_global_binding():
    source_path = (
        HOME
        / "skills"
        / "stock-unified"
        / "scripts"
        / "stock_contract_catalog.py"
    )
    source = source_path.read_text(encoding="utf-8")
    if "_is_mutable_global_agents_path" not in source:
        lines = source.splitlines()
        contexts = []
        for number, line in enumerate(lines, start=1):
            if "business_bindings" in line:
                start = max(1, number - 12)
                end = min(len(lines), number + 28)
                contexts.append((number, lines[start - 1 : end]))
        raise AssertionError(
            "Catalog normalization needs an identity-based historical binding "
            f"filter. business_bindings contexts: {contexts}"
        )
