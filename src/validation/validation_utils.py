import json
import re
from typing import Optional, Any, List, Tuple
import requests
from constants import URL_EXCEPTION_LIST, IGNORE_VALUE_MATCH


class ValidationUtils:
    def __init__(self):
        # URLs that should be skipped during validation
        self.url_exceptions = set(URL_EXCEPTION_LIST)
        # Adding common development and test URLs
        self.url_exceptions.update(
            [
                "localhost",
                "127.0.0.1",
                "example.com",
                "test.com",
            ]
        )

    @staticmethod
    def format_json_path(path: str) -> str:
        """
        Formats a JSON path for readability.
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
        """
        parts = path.split(".")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return None

    @staticmethod
    def format_context(context: dict) -> str:
        """
        Formats a JSON dictionary into a readable string.
        """
        try:
            return json.dumps(context, indent=2)
        except (TypeError, ValueError):
            return str(context)

    @staticmethod
    def is_test_or_staging_key(key: str) -> bool:
        """
        Checks if a key corresponds to a test or staging environment.
        """
        return any(term in key.lower() for term in ["staging", "testnet", "dev"])

    @staticmethod
    def is_placeholder(value: Any) -> bool:
        """
        Checks if a value is a placeholder.
        """
        if isinstance(value, str):
            return bool(re.match(r"\[.*\]", value))
        return False

    def is_exception(self, url: str) -> bool:
        """
        Checks if a URL matches any exceptions in the URL exception list.

        Args:
            url (str): The URL to check

        Returns:
            bool: True if the URL should be excluded from validation
        """
        try:
            return (
                any(exception in url for exception in self.url_exceptions) or "[" in url
            )  # Also skip placeholder URLs
        except Exception:
            return False

    def should_ignore_value_match(self, path: str) -> bool:
        """
        Checks if value matching should be ignored for a given path.
        """
        return any(ignored_path in path for ignored_path in IGNORE_VALUE_MATCH)
