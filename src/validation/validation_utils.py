import json
from typing import Optional


class ValidationUtils:
    @staticmethod
    def format_json_path(path: str) -> str:
        """
        Formats a JSON path for readability.

        Args:
            path (str): The JSON path to format.

        Returns:
            str: A formatted JSON path string.
        """
        parts = path.split(".")
        if len(parts) == 1:
            return f'"{parts[0]}": {{'
        elif len(parts) > 1:
            last_part = parts[-1]
            if "[" in last_part:
                array_part = last_part.split("[")
                return f'"{array_part[0]}": ['
            return f'"{last_part}":'
        return path

    @staticmethod
    def get_parent_path(path: str) -> Optional[str]:
        """
        Extracts the parent path from a given JSON path.

        Args:
            path (str): The JSON path.

        Returns:
            Optional[str]: The parent path, or the original path if no parent exists.
        """
        parts = path.split(".")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return None

    @staticmethod
    def format_context(context: dict) -> str:
        """
        Formats a JSON dictionary into a readable string.

        Args:
            context (dict): The JSON dictionary.

        Returns:
            str: A formatted JSON string.
        """
        try:
            return json.dumps(context, indent=2)
        except (TypeError, ValueError):
            return str(context)

    @staticmethod
    def is_test_or_staging_key(key: str) -> bool:
        """
        Checks if a key corresponds to a test or staging environment.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key is related to test or staging environments, False otherwise.
        """
        return any(term in key.lower() for term in ["staging", "testnet", "dev"])
