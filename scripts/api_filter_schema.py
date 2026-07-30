#!/usr/bin/env python3

import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from yaml import dump, safe_load


def collect_refs(obj: Any, refs: set[str]) -> None:
    """Recursively collect all $ref strings from a schema object."""
    if isinstance(obj, dict):
        if "$ref" in obj:
            refs.add(obj["$ref"])
        for value in obj.values():
            collect_refs(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            collect_refs(item, refs)


def resolve_component_refs(schema: dict[str, Any], refs: set[str]) -> None:
    """
    Expand refs by also collecting refs from the referenced components themselves,
    handling transitive dependencies.
    """
    components = schema.get("components", {})
    visited: set[str] = set()

    def expand(ref_set: set[str]) -> None:
        new_refs = ref_set - visited
        if not new_refs:
            return
        visited.update(new_refs)
        next_refs: set[str] = set()
        for ref in new_refs:
            # Only handle local $refs like #/components/schemas/Foo
            match = re.match(r"^#/components/(\w+)/(.+)$", ref)
            if match:
                section, name = match.group(1), match.group(2)
                component = components.get(section, {}).get(name)
                if component:
                    collect_refs(component, next_refs)
        expand(next_refs)

    expand(refs)
    refs.update(visited)


def filter_components(schema: dict[str, Any], refs: set[str]) -> dict[str, Any]:
    """Return a filtered components dict containing only referenced entries."""
    components = schema.get("components", {})
    filtered = {}

    for section, entries in components.items():
        if section in ("securitySchemes",):
            filtered[section] = entries
            continue
        if not isinstance(entries, dict):
            continue
        kept = {}
        for name, definition in entries.items():
            ref_key = f"#/components/{section}/{name}"
            if ref_key in refs:
                kept[name] = definition
        if kept:
            filtered[section] = kept

    return filtered


def filter_schema(schema: dict[str, Any], operation_ids: set[str]) -> dict[str, Any]:
    filtered_paths = {}
    all_refs: set[str] = set()

    for path, path_item in schema.get("paths", {}).items():
        filtered_methods = {}
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            if operation.get("operationId") in operation_ids:
                filtered_methods[method] = operation
                collect_refs(operation, all_refs)

        # Preserve path-level fields (parameters, servers, summary) if any
        # operation in this path was kept
        if filtered_methods:
            path_level = {
                k: v
                for k, v in path_item.items()
                if k not in ("get", "put", "post", "delete", "options", "head", "patch", "trace")
            }
            collect_refs(path_level, all_refs)
            filtered_paths[path] = {**path_level, **filtered_methods}

    # Resolve transitive component references
    resolve_component_refs(schema, all_refs)

    result = {key: schema[key] for key in ("openapi", "info", "servers") if key in schema}
    result["paths"] = filtered_paths

    filtered_components = filter_components(schema, all_refs)
    if filtered_components:
        result["components"] = filtered_components

    return result


def main(input_path: str, output_path: str, ids_path: str) -> None:
    schema = safe_load(Path(input_path).read_text())
    operation_ids = {
        line.strip() for line in Path(ids_path).read_text().splitlines() if line.strip()
    }

    filtered = filter_schema(deepcopy(schema), operation_ids)
    Path(output_path).write_text(dump(filtered, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    if len(sys.argv) != 4:  # noqa: PLR2004
        print("Usage: python filter_openapi.py <input_schema> <output_schema> <operationids_file>")
        sys.exit(1)
    main(*sys.argv[1:])
