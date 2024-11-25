import json
from pathlib import Path
from typing import Any, Dict

from validation.validation_utils import ValidationUtils


def filter_non_production(data: dict, utils: ValidationUtils) -> dict:
    """
    Filters out non-production configurations from the JSON data.

    Args:
        data (dict): The original JSON data.
        utils (ValidationUtils): Utility instance for helper methods.

    Returns:
        dict: Filtered JSON data containing only production configurations.
    """
    if not isinstance(data, dict):
        return data

    filtered_data = {}
    for key, value in data.items():
        # Skip test/staging environments and related configs
        if utils.is_test_or_staging_key(key):
            continue

        if isinstance(value, dict):
            # For environments section, check the isMainNet flag
            if key == "environments":
                filtered_env = {
                    env_key: env_value
                    for env_key, env_value in value.items()
                    if env_value.get("isMainNet", False)
                }
                filtered_data[key] = filtered_env
            else:
                filtered_value = filter_non_production(value, utils)
                if filtered_value:  # Only add if there's content after filtering
                    filtered_data[key] = filtered_value
        else:
            filtered_data[key] = value

    return filtered_data


def load_json(file_path: Path, utils: Any) -> (Dict, Dict[str, int]):
    """
    Loads a JSON file and captures line numbers for all keys in a nested structure.

    Args:
        file_path (Path): Path to the JSON file.
        utils (ValidationUtils): Utility instance for helper methods.

    Returns:
        Tuple[Dict, Dict[str, int]]: Parsed JSON data and a dictionary of line numbers.
    """
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            json_data = json.loads(content)

            # Line numbers dictionary
            line_numbers = {}

            def parse_lines(obj, current_path="", start_line=0):
                """Recursively map line numbers for keys in a JSON object."""
                nonlocal line_numbers
                lines = content.splitlines()
                for i in range(start_line, len(lines)):
                    line = lines[i].strip()
                    if ":" in line:
                        key = line.split(":", 1)[0].strip('" ')
                        path = f"{current_path}.{key}" if current_path else key
                        if path not in line_numbers:
                            line_numbers[path] = i + 1
                            if isinstance(obj, dict) and key in obj:
                                # Recursively handle nested objects
                                parse_lines(
                                    obj[key],
                                    path,
                                    i + 1,
                                )
                        elif isinstance(obj, list):
                            for idx, item in enumerate(obj):
                                sub_path = f"{path}[{idx}]"
                                line_numbers[sub_path] = i + 1

            parse_lines(json_data)

            return json_data, line_numbers

    except Exception as e:
        raise Exception(f"Failed to load {file_path}: {str(e)}")
