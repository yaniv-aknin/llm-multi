import json
import html
import re
from pathlib import Path
from typing import List, Optional
import click

from .format import create_archive_output, extract_single_file


def create_archive(
    files: List[str], basename: bool, basedir: Optional[str], format: str
):
    """Create a archive from input files."""
    items = []

    for file_path in files:
        path = Path(file_path).resolve()

        if basedir:
            try:
                rel_path = path.relative_to(Path(basedir).resolve())
                display_path = str(rel_path)
            except ValueError:
                click.echo(
                    f"Warning: {file_path} does not have prefix {basedir}, skipping",
                    err=True,
                )
                continue
        else:
            display_path = str(path)

        if basename:
            display_path = path.name

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if format == "jsonl":
                item = {"path": display_path, "content": content}
                click.echo(json.dumps(item))
            elif format in ["xml", "xmlish"]:
                tag_name = re.sub(r"[^a-zA-Z0-9_-]", "_", display_path)
                if format == "xml":
                    escaped_content = html.escape(content)
                    click.echo(f"<{tag_name}>\n{escaped_content}\n</{tag_name}>")
                else:  # xmlish
                    click.echo(f"<{tag_name}>\n{content}\n</{tag_name}>")
            else:
                items.append((display_path, content))

        except Exception as e:
            click.echo(f"Warning: Could not read {file_path}: {e}", err=True)

    if format != "jsonl":
        create_archive_output(items, format)


def extract_archive(file_obj, basename: bool, basedir: Optional[str], format: str):
    """Extract files from a archive."""
    content = file_obj.read().strip()

    if format == "jsonl":
        for line in content.split("\n"):
            if not line.strip():
                continue

            try:
                item = json.loads(line)
                path = item["path"]
                file_content = item["content"]
                extract_single_file(path, file_content, basename, basedir)
            except Exception as e:
                click.echo(f"Warning: Could not process line: {e}", err=True)

    elif format == "json":
        try:
            data = json.loads(content)
            for path, file_content in data.items():
                extract_single_file(path, file_content, basename, basedir)
        except Exception as e:
            click.echo(f"Warning: Could not process JSON: {e}", err=True)

    elif format == "jsonarr":
        try:
            data = json.loads(content)
            for i, file_content in enumerate(data):
                path = f"item_{i}.txt"
                extract_single_file(path, file_content, basename, basedir)
        except Exception as e:
            click.echo(f"Warning: Could not process JSON array: {e}", err=True)

    elif format in ["xml", "xmlish"]:
        try:
            pattern = r"<([^>]+)>(.*?)</\1>"
            matches = re.findall(pattern, content, re.DOTALL)
            for tag_name, file_content in matches:
                # Remove only the single newline we added at start and end for formatting
                if file_content.startswith("\n"):
                    file_content = file_content[1:]
                if file_content.endswith("\n"):
                    file_content = file_content[:-1]
                if format == "xml":
                    file_content = html.unescape(file_content)
                path = tag_name.replace("_", ".")
                extract_single_file(path, file_content, basename, basedir)
        except Exception as e:
            click.echo(f"Warning: Could not process XML: {e}", err=True)
