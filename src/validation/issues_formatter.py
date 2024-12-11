from typing import Any, List, Tuple, Dict
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from datetime import datetime


def create_visual_diff(
    structure_issues: List[Tuple[str, str, Dict]],
    url_issues: List[Dict[str, Any]],
    console: Console,
    utils: Any,
    file_1_name: str,
    file_2_name: str,
) -> None:
    """
    Generates a visual representation of validation issues.

    Args:
        structure_issues (List[Tuple[str, str, Dict]]): List of structure validation issues
        url_issues (List[Dict[str, Any]]): List of URL validation issues
        console (Console): Rich Console instance for rendering output
        utils (Any): ValidationUtils instance for utility functions
        file_1_name (str): Name of the first JSON file being compared
        file_2_name (str): Name of the second JSON file being compared
    """
    # Output the names of the files being compared
    console.print("\n")
    console.print(
        Panel.fit(
            f"Comparing files:\n[green]{file_1_name}[/green] vs [yellow]{file_2_name}[/yellow]",
            style="bold blue",
        )
    )
    console.print("\n")

    # Group structure issues
    structure_groups = {"Missing": [], "Mismatch": [], "Structure": []}
    for issue, path, context in structure_issues:
        if "Missing" in issue:
            structure_groups["Missing"].append((issue, path, context))
        elif "mismatch" in issue.lower():
            structure_groups["Mismatch"].append((issue, path, context))
        else:
            structure_groups["Structure"].append((issue, path, context))

    # Group URL issues
    url_groups = {}
    for issue in url_issues:
        issue_type = issue["type"]
        if issue_type not in url_groups:
            url_groups[issue_type] = []
        url_groups[issue_type].append(issue)

    console.print("\n")
    console.print(
        Panel.fit("🔍 Environment Configuration Validation Results", style="bold blue")
    )
    console.print("\n")

    if structure_issues or url_issues:
        issues_tree = Tree("🚨 Detailed Issues")

        # Structure Issues
        if structure_issues:
            structure_branch = issues_tree.add("Structure Validation Issues")
            for group_name, group_issues in structure_groups.items():
                if group_issues:
                    category_branch = structure_branch.add(
                        f"[red]{group_name} Issues ({len(group_issues)})[/red]"
                    )
                    for issue, path, context in group_issues:
                        issue_text = Text(issue, style="bold")
                        issue_node = category_branch.add(issue_text)

                        if path:
                            search_path = utils.format_json_path(path)
                            parent_path = utils.get_parent_path(path)
                            parent_path_formatted = (
                                utils.format_json_path(parent_path)
                                if parent_path
                                else None
                            )

                            search_node = issue_node.add(
                                "[blue]Search for either:[/blue]"
                            )
                            search_node.add(f"1. Exact: {search_path}")
                            if (
                                parent_path_formatted
                                and parent_path_formatted != search_path
                            ):
                                search_node.add(f"2. Parent: {parent_path_formatted}")

                        if context:
                            context_str = utils.format_context(context)
                            context_node = issue_node.add(
                                "[yellow]Expected structure:[/yellow]"
                            )
                            context_node.add(
                                Syntax(context_str, "json", theme="monokai")
                            )

        # URL Issues
        if url_issues:
            url_branch = issues_tree.add("URL Validation Issues")
            for issue_type, type_issues in url_groups.items():
                category_branch = url_branch.add(
                    f"[magenta]{issue_type.replace('_', ' ').title()} Issues ({len(type_issues)})[/magenta]"
                )

                for issue in type_issues:
                    issue_text = Text(f"Path: {issue['path']}", style="bold")
                    issue_node = category_branch.add(issue_text)

                    # URL with highlighting
                    url_text = Text()
                    url_parts = issue["url"].split("/")
                    for part in url_parts:
                        if any(
                            indicator in part.lower()
                            for indicator in ["invalid", "error", "404"]
                        ):
                            url_text.append(f"{part}/", style="bold red")
                        else:
                            url_text.append(f"{part}/", style="green")

                    issue_node.add("URL: ", style="yellow")
                    issue_node.add(url_text)

                    # Details
                    issue_node.add(f"Details: {issue['details']}", style="yellow")
                    issue_node.add(f"Timestamp: {issue['timestamp']}", style="dim")

        console.print(issues_tree)
        console.print("\n")
    else:
        console.print(Panel.fit("✅ All validations passed!", style="bold green"))
