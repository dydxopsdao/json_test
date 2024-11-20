import json
import sys
import re
from typing import Dict, List, Set, Tuple, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint
from rich.syntax import Syntax
from rich.text import Text


class ValidationUtils:
    @staticmethod
    def format_json_path(path: str) -> str:
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
    def get_parent_path(path: str) -> str:
        parts = path.split(".")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return path

    @staticmethod
    def format_context(context: dict) -> str:
        try:
            return json.dumps(context, indent=2)
        except:
            return str(context)

    @staticmethod
    def is_test_or_staging_key(key: str) -> bool:
        return any(term in key.lower() for term in ["staging", "testnet", "dev"])


class EnvConfigValidator:
    def __init__(self, reference_path: Path, deployment_path: Path):
        self.utils = ValidationUtils()
        self.reference_path = reference_path
        self.deployment_path = deployment_path
        self.reference_config = self._load_json(reference_path)
        self.deployment_config = self._load_json(deployment_path)
        self.console = Console()

    def _filter_non_production(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return data

        filtered_data = {}
        for key, value in data.items():
            # Skip test/staging environments and related configs
            if self.utils.is_test_or_staging_key(key):
                continue

            if isinstance(value, dict):
                # For environments section, check isMainNet flag
                if key == "environments":
                    filtered_env = {}
                    for env_key, env_value in value.items():
                        if env_value.get("isMainNet", False):
                            filtered_env[env_key] = env_value
                    filtered_data[key] = filtered_env
                else:
                    filtered_value = self._filter_non_production(value)
                    if filtered_value:  # Only add if there's content after filtering
                        filtered_data[key] = filtered_value
            else:
                filtered_data[key] = value

        return filtered_data

    def _load_json(self, file_path: Path) -> dict:
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                content = f.read()
                json_data = json.loads(content)

                # Store line numbers for context
                self.line_numbers = {}
                self.file_lines = content.split("\n")
                current_path = []

                for line_num, line in enumerate(self.file_lines, 1):
                    stripped = line.strip()
                    if ":" in stripped and not stripped.startswith("{"):
                        key = stripped.split(":", 1)[0].strip().strip('"')
                        current_path.append(key)
                        self.line_numbers[".".join(current_path)] = line_num
                    if "}" in stripped:
                        if current_path:
                            current_path.pop()

                # Filter out non-production data
                return self._filter_non_production(json_data)

        except Exception as e:
            raise Exception(f"Failed to load {file_path}: {str(e)}")

    def _get_context(self, path: str, ref_config: dict) -> dict:
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

    def _is_placeholder(self, value: str) -> bool:
        if isinstance(value, str):
            return bool(re.match(r"\[.*\]", value))
        return False

    def _is_mainnet_id(self, key: str) -> bool:
        mainnet_patterns = [
            "[mainnet chain id]",
            "dydx-mainnet-1",
            "dydxprotocol-mainnet",
        ]
        return any(pattern in key for pattern in mainnet_patterns)

    def _find_matching_key(self, ref_key: str, dep_keys: set) -> str:
        if self._is_mainnet_id(ref_key):
            for key in dep_keys:
                if self._is_mainnet_id(key):
                    return key
        return ref_key

    def _validate_structure(
        self, ref: Any, dep: Any, path: str = ""
    ) -> List[Tuple[str, str, dict]]:
        issues = []

        if isinstance(ref, dict) and isinstance(dep, dict):
            ref_keys = set(ref.keys())
            dep_keys = set(dep.keys())

            if path == "":
                required_sections = {
                    "apps",
                    "tokens",
                    "wallets",
                    "governance",
                    "environments",
                }
                missing_required = required_sections - dep_keys
                for section in missing_required:
                    context = self._get_context(section, self.reference_config)
                    issues.append(
                        (f"Missing required section: {section}", section, context)
                    )

            for key in ref_keys:
                # Skip validation for test/staging keys
                if self.utils.is_test_or_staging_key(key):
                    continue

                matching_key = self._find_matching_key(key, dep_keys)
                new_path = f"{path}.{key}" if path else key

                if matching_key not in dep:
                    if not self._is_mainnet_id(key):
                        context = self._get_context(new_path, self.reference_config)
                        issues.append((f"Missing key: {new_path}", new_path, context))
                else:
                    if isinstance(ref[key], str) and self._is_placeholder(ref[key]):
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
                            self._validate_structure(
                                ref[key], dep[matching_key], new_path
                            )
                        )

        elif isinstance(ref, list) and isinstance(dep, list):
            pass
        elif not self._is_placeholder(ref):
            if ref != dep and path in self._get_critical_paths():
                issues.append(
                    (
                        f"Value mismatch at {path}: expected {ref}, got {dep}",
                        path,
                        {"expected": ref, "got": dep},
                    )
                )

        return issues

    def _get_critical_paths(self) -> Set[str]:
        return {
            "wallets.*.signTypedDataAction",
            "wallets.*.signTypedDataDomainName",
            "governance.*.newMarketProposal.initialDepositAmount",
            "governance.*.newMarketProposal.delayBlocks",
        }

    def _create_visual_diff(self, issues: List[Tuple[str, str, dict]]) -> None:
        console = Console()
        issue_groups = {"Missing": [], "Mismatch": [], "Structure": []}

        for issue, path, context in issues:
            if "Missing" in issue:
                issue_groups["Missing"].append((issue, path, context))
            elif "mismatch" in issue:
                issue_groups["Mismatch"].append((issue, path, context))
            else:
                issue_groups["Structure"].append((issue, path, context))

        console.print("\n")
        console.print(
            Panel.fit(
                "🔍 Environment Configuration Validation Results", style="bold blue"
            )
        )
        console.print("\n")

        if issues:
            issues_tree = Tree("🚨 Detailed Issues")

            for issue_type, type_issues in issue_groups.items():
                if type_issues:
                    category_branch = issues_tree.add(
                        f"[red]{issue_type} Issues ({len(type_issues)})[/red]"
                    )
                    for issue, path, context in type_issues:
                        issue_text = Text(issue)
                        issue_node = category_branch.add(issue_text)

                        search_path = self.utils.format_json_path(path)
                        parent_path = self.utils.format_json_path(
                            self.utils.get_parent_path(path)
                        )

                        search_node = issue_node.add("[blue]Search for either:[/blue]")
                        search_node.add(f"1. Exact: {search_path}")
                        if parent_path != search_path:
                            search_node.add(f"2. Parent: {parent_path}")

                        if context:
                            context_str = self.utils.format_context(context)
                            context_node = issue_node.add(
                                "[yellow]Expected structure:[/yellow]"
                            )
                            context_node.add(
                                Syntax(context_str, "json", theme="monokai")
                            )

            console.print(issues_tree)
            console.print("\n")
        
        else:
            console.print(Panel.fit("✅ All validations passed!", style="bold green"))

    def validate(self) -> Tuple[bool, List[Tuple[str, str, dict]]]:
        issues = []
        structure_issues = self._validate_structure(
            self.reference_config, self.deployment_config
        )
        issues.extend(structure_issues)
        self._create_visual_diff(issues)
        return len(issues) == 0, issues


def main():
    if len(sys.argv) != 3:
        console = Console()
        console.print(
            "[red]Usage: python env_validator.py <reference_env.json> <deployment_env.json>[/red]"
        )
        sys.exit(1)

    validator = EnvConfigValidator(Path(sys.argv[1]), Path(sys.argv[2]))
    is_valid, _ = validator.validate()
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
