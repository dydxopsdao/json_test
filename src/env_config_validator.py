import sys
from pathlib import Path
from typing import List, Tuple, Optional
from rich.console import Console

from validation.json_loader import load_json
from validation.validation_utils import ValidationUtils
from validation.structure_validator import validate_structure
from validation.url_validator import URLValidator
from validation.issues_formatter import create_visual_diff


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

        # Initialize validators
        self.url_validator = URLValidator(self.utils)

        # Load JSON data and line numbers
        self.reference_config, self.reference_line_numbers = load_json(
            reference_path, self.utils
        )
        self.deployment_config, _ = load_json(deployment_path, self.utils)

    def validate(
        self, skip_structure: bool = False, skip_urls: bool = False
    ) -> Tuple[bool, Optional[List[Tuple[str, str, dict]]], Optional[List[dict]]]:
        """
        Validates the deployment configuration against the reference configuration
        and checks URLs in the deployment configuration.

        Args:
            skip_structure (bool): If True, skips structure validation
            skip_urls (bool): If True, skips URL validation

        Returns:
            Tuple containing:
            - bool: True if all enabled validations passed
            - Optional[List[Tuple[str, str, dict]]]: Structure validation issues (None if skipped)
            - Optional[List[dict]]: URL validation issues (None if skipped)
        """
        structure_issues = None
        url_issues = None

        # Structure validation (comparing against reference)
        if not skip_structure:
            structure_issues = (
                validate_structure(
                    self.reference_config,
                    self.deployment_config,
                    self.utils,
                    self.reference_line_numbers,
                )
                or []
            )

        # URL validation (only on deployment config)
        if not skip_urls:
            self.console.print(
                "\n[bold blue]Validating URLs in deployment configuration...[/bold blue]"
            )
            url_issues = self.url_validator.validate_urls(self.deployment_config)

        # Create visual diff
        create_visual_diff(
            structure_issues or [],
            url_issues or [],
            self.console,
            self.utils,
            file_1_name=self.reference_path.name,
            file_2_name=self.deployment_path.name,
        )

        # Validation passes if there are no issues in any enabled validation
        is_valid = (
            skip_structure or not structure_issues or len(structure_issues) == 0
        ) and (skip_urls or not url_issues or len(url_issues) == 0)

        return is_valid, structure_issues, url_issues


def main():
    """
    Entry point for the script. Handles CLI arguments and executes validation.
    """
    if len(sys.argv) < 3:
        console = Console()
        console.print(
            "[red]Usage: python env_validator.py <reference_env.json> <deployment_env.json> [--skip-structure] [--skip-urls][/red]"
        )
        sys.exit(1)

    reference_path = Path(sys.argv[1])
    deployment_path = Path(sys.argv[2])

    # Parse optional flags
    skip_structure = "--skip-structure" in sys.argv
    skip_urls = "--skip-urls" in sys.argv

    validator = EnvConfigValidator(reference_path, deployment_path)
    is_valid, _, _ = validator.validate(
        skip_structure=skip_structure, skip_urls=skip_urls
    )

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
