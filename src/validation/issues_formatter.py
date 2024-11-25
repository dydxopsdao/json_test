from typing import Any, List, Tuple, Dict
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax


def create_visual_diff(
    issues: List[Tuple[str, str, Dict]],
    console: Console,
    utils: Any,
) -> None:
    """
    Generates a visual representation of validation issues.

    Args:
        issues (List[Tuple[str, str, Dict]]): List of issues with their paths and context.
        console (Console): Rich Console instance for rendering output.
        utils (Any): ValidationUtils instance for utility functions.
    """
    issue_groups = {"Missing": [], "Mismatch": [], "Structure": []}

    for issue, path, context in issues:
        if "Missing" in issue:
            issue_groups["Missing"].append((issue, path, context))
        elif "mismatch" in issue.lower():
            issue_groups["Mismatch"].append((issue, path, context))
        else:
            issue_groups["Structure"].append((issue, path, context))

    console.print("\n")
    console.print(
        Panel.fit("🔍 Environment Configuration Validation Results", style="bold blue")
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

                    # Only format paths if they are not None
                    if path:
                        search_path = utils.format_json_path(path)
                        parent_path = utils.get_parent_path(path)
                        parent_path_formatted = (
                            utils.format_json_path(parent_path) if parent_path else None
                        )

                        search_node = issue_node.add("[blue]Search for either:[/blue]")
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
                        context_node.add(Syntax(context_str, "json", theme="monokai"))

        console.print(issues_tree)
        console.print("\n")
    else:
        console.print(Panel.fit("✅ All validations passed!", style="bold green"))
