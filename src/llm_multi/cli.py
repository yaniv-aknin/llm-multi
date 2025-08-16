import click
import llm

from .archive import create_archive, extract_archive
from .map import map_items


@llm.hookimpl
def register_commands(cli):
    @cli.command(name="archive")
    @click.argument("files", nargs=-1, type=click.Path())
    @click.option("--create", is_flag=True, help="Create an archive from files")
    @click.option("--extract", is_flag=True, help="Extract files from an archive")
    @click.option(
        "--basename",
        is_flag=True,
        help="For create: strip path and use only filename. For extract: ignore paths, write only filenames to current directory",
    )
    @click.option(
        "--basedir",
        type=str,
        help="Strip this prefix from paths, refuse to process files without this prefix",
    )
    @click.option(
        "--format",
        type=click.Choice(["jsonl", "json", "jsonarr", "xml", "xmlish"]),
        default="jsonl",
        help="Output format",
    )
    def archive(files, create, extract, basename, basedir, format):
        """Bundle files into JSONL format or extract files from a JSONL archive."""
        if extract and create:
            raise click.ClickException("Cannot use both --create and --extract")

        if extract:
            if not files:
                import sys

                extract_archive(sys.stdin, basename, basedir, format)
            else:
                with open(files[0], "r", encoding="utf-8") as f:
                    extract_archive(f, basename, basedir, format)
        elif create or not extract:
            create_archive(files, basename, basedir, format)

    @cli.command(name="map")
    @click.argument("jsonl_file", type=str)
    @click.argument("prompt_template", type=str, required=False, default="")
    @click.option("--model", "-m", default="gpt-4o-mini", help="Model to use")
    @click.option(
        "--temperature",
        "-t",
        type=float,
        default=0.0,
        help="Temperature for generation",
    )
    @click.option("--tokens", type=int, default=15000, help="Max tokens")
    @click.option(
        "--concurrency",
        "-c",
        type=int,
        default=16,
        help="Number of concurrent requests",
    )
    @click.option("--output", "-o", type=click.Path(), help="Write output to file")
    @click.option(
        "--branches",
        type=int,
        help="Repeat content this many times, prefix the base filename with {i}_",
    )
    @click.option("--input", is_flag=True, help="Include original input in output")
    @click.option(
        "--format",
        type=click.Choice(["jsonl", "json", "jsonarr"]),
        help="Set both input and output format",
    )
    @click.option(
        "--iformat",
        type=click.Choice(["jsonl", "json", "jsonarr"]),
        default="jsonl",
        help="Input format",
    )
    @click.option(
        "--oformat",
        type=click.Choice(["jsonl", "json", "jsonarr"]),
        default="jsonl",
        help="Output format",
    )
    def map_command(
        jsonl_file,
        prompt_template,
        model,
        temperature,
        tokens,
        concurrency,
        output,
        branches,
        input,
        format,
        iformat,
        oformat,
    ):
        """Apply an LLM prompt to each item in a JSON structure or repeated content."""
        if format:
            iformat = oformat = format

        if input and oformat in ["json", "jsonarr"]:
            raise click.ClickException(
                "Cannot use --input with --json or --jsonarr output formats"
            )

        map_items(
            jsonl_file,
            prompt_template,
            model,
            temperature,
            tokens,
            concurrency,
            output,
            branches or 1,
            input,
            iformat,
            oformat,
        )
