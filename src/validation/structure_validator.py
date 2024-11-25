import re
from typing import Any, Dict, List, Tuple, Set
from constants import CRITICAL_PATHS, MAINNET_PATTERNS
from validation.validation_utils import ValidationUtils


def validate_structure(
    ref: Any,
    dep: Any,
    utils: ValidationUtils,
    line_numbers: Dict[str, int],
    path: str = "",
) -> List[Tuple[str, str, dict]]:
    """
    Validates the structure of the deployment configuration against the reference configuration.

    Args:
        ref (Any): Reference configuration.
        dep (Any): Deployment configuration.
        utils (ValidationUtils): Utility class for helper methods.
        line_numbers (Dict[str, int]): Line numbers of keys in the reference JSON.
        path (str, optional): Current path in the configuration tree. Defaults to "".

    Returns:
        List[Tuple[str, str, dict]]: List of validation issues.
    """
    issues = []

    if isinstance(ref, dict) and isinstance(dep, dict):
        ref_keys = set(ref.keys())
        dep_keys = set(dep.keys())

        for key in ref_keys:
            if utils.is_test_or_staging_key(key):
                continue

            matching_key = _find_matching_key(key, dep_keys)
            new_path = f"{path}.{key}" if path else key

            if matching_key not in dep:
                # Missing key: line number from the reference JSON
                line_num = line_numbers.get(new_path, "Unknown")
                context = _get_context(new_path, ref)
                issues.append(
                    (
                        f"Missing key: {new_path} (Reference Line: {line_num})",
                        new_path,
                        context,
                    )
                )
            else:
                # Validate deeper for matched keys
                if isinstance(ref[key], str) and _is_placeholder(ref[key]):
                    if not isinstance(dep[matching_key], str):
                        issues.append(
                            (
                                f"Type mismatch at {new_path}: expected string, got {type(dep[matching_key]).__name__}",
                                new_path,
                                {
                                    "expected": "string",
                                    "got": type(dep[matching_key]).__name__,
                                },
                            )
                        )
                else:
                    issues.extend(
                        validate_structure(
                            ref[key], dep[matching_key], utils, line_numbers, new_path
                        )
                    )

    elif isinstance(ref, list) and isinstance(dep, list):
        for idx, item in enumerate(ref):
            if idx < len(dep):
                issues.extend(
                    validate_structure(
                        item, dep[idx], utils, line_numbers, f"{path}[{idx}]"
                    )
                )
            else:
                # Missing list item: line number from the reference JSON
                line_num = line_numbers.get(f"{path}[{idx}]", "Unknown")
                issues.append(
                    (
                        f"Missing list item at {path}[{idx}] (Reference Line: {line_num})",
                        f"{path}[{idx}]",
                        {"expected": item},
                    )
                )
    elif not _is_placeholder(ref):
        # Value mismatch for critical paths: line number from the reference JSON
        if ref != dep and path in CRITICAL_PATHS:
            line_num = line_numbers.get(path, "Unknown")
            issues.append(
                (
                    f"Value mismatch at {path}: expected {ref}, got {dep} (Reference Line: {line_num})",
                    path,
                    {"expected": ref, "got": dep},
                )
            )

    return issues


def _get_context(path: str, ref_config: dict) -> dict:
    """
    Gets the context for a given path in the reference configuration.

    Args:
        path (str): The JSON path.
        ref_config (dict): Reference configuration.

    Returns:
        dict: Context dictionary.
    """
    try:
        parts = path.split(".")
        current = ref_config
        for part in parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return {}
        if parts[-1] in current:
            return {parts[-1]: current[parts[-1]]}
    except:
        pass
    return {}


def _is_placeholder(value: str) -> bool:
    """
    Checks if a value is a placeholder.

    Args:
        value (str): The value to check.

    Returns:
        bool: True if the value is a placeholder, False otherwise.
    """
    if isinstance(value, str):
        return bool(re.match(r"\[.*\]", value))
    return False


def _is_mainnet_id(key: str) -> bool:
    """
    Checks if a key corresponds to a mainnet identifier.

    Args:
        key (str): The key to check.

    Returns:
        bool: True if the key matches a mainnet pattern, False otherwise.
    """
    return any(pattern in key for pattern in MAINNET_PATTERNS)


def _find_matching_key(ref_key: str, dep_keys: Set[str]) -> str:
    """
    Finds the best match for a reference key in the set of deployment keys.

    Args:
        ref_key (str): The reference key.
        dep_keys (Set[str]): Set of deployment keys.

    Returns:
        str: The matching deployment key, or the reference key if no match is found.
    """
    if _is_mainnet_id(ref_key):
        for key in dep_keys:
            if _is_mainnet_id(key):
                return key
    return ref_key
