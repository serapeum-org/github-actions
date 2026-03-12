"""Generate markdown reference tables from action.yml files.

Parses each composite action's action.yml and produces a standardized
markdown file with inputs table, outputs table, and usage snippet.

Usage:
    python scripts/generate_action_docs.py
"""

import os
import re
from pathlib import Path

# We use a minimal YAML parser to avoid external dependencies.
# action.yml files are simple enough for regex-based extraction.


def parse_action_yml(path: str) -> dict:
    """Parse an action.yml file and extract metadata, inputs, and outputs."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    result = {
        "name": "",
        "description": "",
        "inputs": [],
        "outputs": [],
        "path": path,
    }

    # Extract top-level name and description
    name_match = re.search(r"^name:\s*['\"]?(.*?)['\"]?\s*$", content, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1).strip().strip("'\"")

    desc_match = re.search(
        r"^description:\s*['\"]?(.*?)['\"]?\s*$", content, re.MULTILINE
    )
    if desc_match:
        result["description"] = desc_match.group(1).strip().strip("'\"")

    # Extract inputs section (capture until next top-level key or end)
    inputs_match = re.search(
        r"^inputs:\s*\n((?:(?:[ \t]+.*|[ \t]*)\n)*)", content, re.MULTILINE
    )
    if inputs_match:
        inputs_block = inputs_match.group(1)
        result["inputs"] = _parse_params(inputs_block)

    # Extract outputs section
    outputs_match = re.search(
        r"^outputs:\s*\n((?:(?:[ \t]+.*|[ \t]*)\n)*)", content, re.MULTILINE
    )
    if outputs_match:
        outputs_block = outputs_match.group(1)
        result["outputs"] = _parse_params(outputs_block)

    return result


def _parse_params(block: str) -> list[dict]:
    """Parse an inputs or outputs YAML block into a list of parameter dicts."""
    params = []
    current = None
    multiline_prop = None  # Track which property is being read as multiline

    for line in block.split("\n"):
        # Top-level key (input/output name) - exactly 2 spaces indent
        key_match = re.match(r"^  (\w[\w-]*):\s*$", line)
        if key_match:
            multiline_prop = None
            if current:
                params.append(current)
            current = {
                "name": key_match.group(1),
                "description": "",
                "required": False,
                "default": "",
            }
            continue

        if current is None:
            continue

        # If we're reading a multiline block (description: |), collect lines
        if multiline_prop:
            # Multiline continuation: 6+ spaces indent or blank line
            if re.match(r"^\s{6,}", line) or line.strip() == "":
                text = line.strip()
                if text:
                    if current[multiline_prop]:
                        current[multiline_prop] += " " + text
                    else:
                        current[multiline_prop] = text
                continue
            else:
                multiline_prop = None
                # Fall through to parse this line normally

        # Sub-properties - 4+ spaces indent
        prop_match = re.match(
            r"^\s{4,}(\w[\w-]*):\s*(.*?)\s*$", line
        )
        if prop_match:
            prop_name = prop_match.group(1)
            prop_value = prop_match.group(2).strip().strip("'\"")

            # Detect multiline block scalar (value is | or >)
            if prop_value in ("|", ">", "|+", "|-", ">+", ">-"):
                if prop_name in ("description", "required", "default"):
                    multiline_prop = prop_name
                    current[prop_name] = ""
                continue

            if prop_name == "description":
                current["description"] = prop_value
            elif prop_name == "required":
                current["required"] = prop_value.lower() == "true"
            elif prop_name == "default":
                current["default"] = prop_value

    if current:
        params.append(current)

    return params


def action_path_to_ref(action_dir: str) -> str:
    """Convert an action directory path to the GitHub reference format.

    Example: actions/python-setup/pip -> python-setup/pip
    """
    rel = action_dir.replace("\\", "/")
    if rel.startswith("actions/"):
        rel = rel[len("actions/"):]
    return rel


def _version_tag(ref: str) -> str:
    """Build the namespaced version tag from an action reference path.

    Examples:
        python-setup/pip  -> pip/v1
        mkdocs-deploy     -> mkdocs-deploy/v1
        release/github    -> release-github/v1
    """
    parts = ref.strip("/").split("/")
    if len(parts) == 1:
        return f"{parts[0]}/v1"
    # Use the last segment for single-depth (python-setup/pip -> pip)
    # Use hyphen-joined for deeper paths (release/github -> release-github)
    if parts[0] == "python-setup":
        return f"{parts[-1]}/v1"
    return f"{'-'.join(parts)}/v1"


def generate_reference_md(action: dict, action_dir: str) -> str:
    """Generate a markdown reference page for a single action."""
    ref = action_path_to_ref(action_dir)
    tag = _version_tag(ref)
    lines = [
        f"# {action['name']}",
        "",
        f"> {action['description']}",
        "",
        "## Usage",
        "",
        "```yaml",
        f"- uses: Serapieum-of-alex/github-actions/actions/{ref}@{tag}",
    ]

    # Add a `with:` block showing only required inputs and those with defaults
    if action["inputs"]:
        lines.append("  with:")
        for inp in action["inputs"]:
            if inp["required"]:
                lines.append(f"    {inp['name']}: # required")
            elif inp["default"]:
                lines.append(f"    {inp['name']}: '{inp['default']}'")
            else:
                lines.append(f"    {inp['name']}: ''")

    lines.extend(["```", ""])

    # Inputs table
    if action["inputs"]:
        lines.extend([
            "## Inputs",
            "",
            "| Input | Description | Required | Default |",
            "|-------|-------------|:--------:|---------|",
        ])
        for inp in action["inputs"]:
            req = "Yes" if inp["required"] else "No"
            default = f"`{inp['default']}`" if inp["default"] else "-"
            # Use first sentence only to keep table readable
            desc = inp["description"].split(". ")[0].split(".\n")[0]
            if desc and not desc.endswith("."):
                desc += ""
            # Escape pipe characters for markdown tables
            desc = desc.replace("|", "\\|")
            lines.append(f"| `{inp['name']}` | {desc} | {req} | {default} |")
        lines.append("")

    # Outputs table
    if action["outputs"]:
        lines.extend([
            "## Outputs",
            "",
            "| Output | Description |",
            "|--------|-------------|",
        ])
        for out in action["outputs"]:
            lines.append(f"| `{out['name']}` | {out['description']} |")
        lines.append("")

    return "\n".join(lines)


def discover_actions(root: str) -> list[tuple[str, str]]:
    """Find all action.yml files and return (action_dir, yml_path) pairs."""
    actions = []
    for dirpath, _, filenames in os.walk(os.path.join(root, "actions")):
        if "action.yml" in filenames:
            yml_path = os.path.join(dirpath, "action.yml")
            rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
            actions.append((rel_dir, yml_path))
    actions.sort()
    return actions


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(root, "docs", "reference")
    os.makedirs(output_dir, exist_ok=True)

    actions = discover_actions(root)
    index_entries = []

    for action_dir, yml_path in actions:
        action = parse_action_yml(yml_path)
        md_content = generate_reference_md(action, action_dir)

        # Build output filename from action path
        # e.g. actions/python-setup/pip -> python-setup-pip.md
        safe_name = action_dir.replace("actions/", "").replace("/", "-")
        out_path = os.path.join(output_dir, f"{safe_name}.md")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"Generated: {out_path}")
        index_entries.append((action["name"], safe_name, action["description"]))

    # Generate reference index
    index_lines = [
        "# Actions Reference",
        "",
        "Auto-generated from `action.yml` definitions.",
        "",
        "| Action | Description |",
        "|--------|-------------|",
    ]
    for name, safe_name, desc in index_entries:
        index_lines.append(f"| [{name}]({safe_name}.md) | {desc} |")

    index_path = os.path.join(output_dir, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")

    print(f"Generated index: {index_path}")
    print(f"Total actions documented: {len(actions)}")


if __name__ == "__main__":
    main()
