import json
import html
import re
import sys
from typing import List, Optional
from pathlib import Path
import click


def parse_input(input_file: str, iformat: str) -> List[dict]:
    """Parse input based on format."""
    if input_file == "-":
        content = sys.stdin.read()
    else:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

    items = []

    if iformat == "jsonl":
        for line in content.split("\n"):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                items.append(item)
            except Exception as e:
                click.echo(f"Warning: Could not parse line: {e}", err=True)

    elif iformat == "json":
        try:
            data = json.loads(content)
            for path, file_content in data.items():
                items.append({"path": path, "content": file_content})
        except Exception as e:
            click.echo(f"Warning: Could not parse JSON: {e}", err=True)

    elif iformat == "jsonarr":
        try:
            data = json.loads(content)
            for i, file_content in enumerate(data):
                items.append({"path": f"item_{i}", "content": file_content})
        except Exception as e:
            click.echo(f"Warning: Could not parse JSON array: {e}", err=True)

    elif iformat in ["xml", "xmlish"]:
        try:
            pattern = r"<([^>]+)>(.*?)</\1>"
            matches = re.findall(pattern, content, re.DOTALL)
            for tag_name, file_content in matches:
                # Remove only the single newline we may have added at start and end for formatting
                if file_content.startswith("\n"):
                    file_content = file_content[1:]
                if file_content.endswith("\n"):
                    file_content = file_content[:-1]
                if iformat == "xml":
                    file_content = html.unescape(file_content)
                path = tag_name.replace("_", ".")
                items.append({"path": path, "content": file_content})
        except Exception as e:
            click.echo(f"Warning: Could not parse XML: {e}", err=True)

    return items


def output_results(results: List[dict], output_file: Optional[str], oformat: str):
    """Output results in specified format."""
    if oformat == "jsonl":
        for result in results:
            output_line = json.dumps(result)
            if output_file:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(output_line + "\n")
            else:
                click.echo(output_line)

    elif oformat == "json":
        json_result = {}
        for result in results:
            path = result["path"]
            if "error" in result:
                json_result[path] = {"error": result["error"]}
            else:
                json_result[path] = result["content"]

        output_content = json.dumps(json_result)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_content)
        else:
            click.echo(output_content)

    elif oformat == "jsonarr":
        json_result = []
        for result in results:
            if "error" in result:
                json_result.append({"error": result["error"]})
            else:
                json_result.append(result["content"])

        output_content = json.dumps(json_result)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_content)
        else:
            click.echo(output_content)


def create_archive_output(items: List[tuple], format: str):
    """Output archive data in specified format."""
    if format == "jsonl":
        for display_path, content in items:
            item = {"path": display_path, "content": content}
            click.echo(json.dumps(item))
    elif format == "json":
        result = {item[0]: item[1] for item in items}
        click.echo(json.dumps(result))
    elif format == "jsonarr":
        result = [item[1] for item in items]
        click.echo(json.dumps(result))


def extract_single_file(
    path: str, content: str, basename: bool, basedir: Optional[str]
):
    """Extract a single file."""
    if basename:
        output_path = Path(Path(path).name)
    else:
        if basedir:
            output_path = Path(basedir) / path
        else:
            output_path = Path(path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write(content)

    click.echo(f"Extracted: {output_path}")
