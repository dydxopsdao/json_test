import sys
from pathlib import Path
from typing import List, Tuple
from rich.console import Console

from validation.json_loader import load_json  # Refactored JSON loading logic
from validation.validation_utils import ValidationUtils  # Refactored utilities
from constants import MAINNET_PATTERNS  # Patterns for mainnet keys
from validation.structure_validator import validate_structure  # Validation logic
from validation.issues_formatter import create_visual_diff  # Visualize issues


class EnvConfigValidator:
    def __init__(self, reference_path: Path, deployment_path: Path):
        """
        Initializes the EnvConfigValidator with paths to the reference
        and deployment JSON files.

        Args:
            reference_path (Path): Path to the reference configuration file.
            deployment_path (Path): Path to the deployment configuration file.
        """
        self.utils = ValidationUtils()
        self.console = Console()
        self.reference_path = reference_path
        self.deployment_path = deployment_path

        # Load JSON data and line numbers
        self.reference_config, self.reference_line_numbers = load_json(
            reference_path, self.utils
        )
        self.deployment_config, _ = load_json(deployment_path, self.utils)

    def _find_matching_key(self, ref_key: str, dep_keys: set) -> str:
        """
        Finds the best match for a key in the deployment keys based on mainnet patterns.

        Args:
            ref_key (str): The reference key to match.
            dep_keys (set): The set of deployment keys.

        Returns:
            str: The best matching key, or the original reference key if no match is found.
        """
        if any(pattern in ref_key for pattern in MAINNET_PATTERNS):
            for key in dep_keys:
                if any(pattern in key for pattern in MAINNET_PATTERNS):
                    return key
        return ref_key

    def validate(self) -> Tuple[bool, List[Tuple[str, str, dict]]]:
        """
        Validates the deployment configuration against the reference configuration.

        Returns:
            Tuple[bool, List[Tuple[str, str, dict]]]: A tuple containing:
                - A boolean indicating if the validation passed.
                - A list of issues identified during validation.
        """
        issues = validate_structure(
            self.reference_config,
            self.deployment_config,
            self.utils,
            self.reference_line_numbers,
        )
        create_visual_diff(
            issues,
            self.console,
            self.utils,
            file_1_name=self.reference_path.name,
            file_2_name=self.deployment_path.name,
        )
        return len(issues) == 0, issues


def main():
    """
    Entry point for the script. Handles CLI arguments and executes validation.
    """
    if len(sys.argv) != 3:
        console = Console()
        console.print(
            "[red]Usage: python env_validator.py <reference_env.json> <deployment_env.json>[/red]"
        )
        sys.exit(1)

    reference_path = Path(sys.argv[1])
    deployment_path = Path(sys.argv[2])

    validator = EnvConfigValidator(reference_path, deployment_path)
    is_valid, _ = validator.validate()
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
