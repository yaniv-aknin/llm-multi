# llm-multi

A plugin for [LLM](https://llm.datasette.io/) that combines file bundling and LLM mapping capabilities into two complementary commands: `llm archive` and `llm map`.

## Commands

### `llm archive`

Bundle files into JSONL format or extract files from a JSONL archive:

```bash
llm archive [files...]
```

**Options:**

- `--create` - Create an archive from files (default)
- `--extract` - Extract files from an archive (exclusive with --create)
- `--basename` - For create: strip path and use only filename. For extract: ignore paths, write only filenames to current directory (last copy wins on collisions)
- `--basedir <str>` - For create and extract: strip this prefix from paths, refuse to process files without this prefix, printing warnings instead
- `--format` - Output format: `jsonl`, `json`, `jsonarr`, `xml`, `xmlish`

### `llm map`

Apply an LLM prompt to each item in a JSON structure or repeated content:

```bash
llm map data.jsonl "Summarize this: {item}"
```

The item will be inserted at the first `{item}` in the prompt. If no `{item}` exists, it will be inserted at the end, as `\n{item}`.

**Options:**

- `--model, -m` - Model to use (default: gpt-4o-mini)
- `--temperature, -t` - Temperature for generation (default: 0.0)
- `--tokens` - Max tokens (default: 15000)
- `--concurrency, -c` - Number of concurrent requests (default: 16)
- `--output, -o` - Write output to file
- `--branches` - Repeat content this many times, prefix the base filename with `{i}_`
- `--content` - Include original content in output (incompatible with `--json`/`--jsonarr` output formats)
- `--format` - Set both input and output format: `jsonl` (default), `json`, `jsonarr`
- `--iformat` - Input format: `jsonl` (default), `json`, `jsonarr`
- `--oformat` - Output format: `jsonl` (default), `json`, `jsonarr`

### Format descriptions

JSON based formats, useful for piping into `map` -

- `jsonl`: One JSON object per line with `path` and `content` fields
- `json`: Single JSON object with filenames as keys and content as values
- `jsonarr`: JSON array containing only content (no filenames)

XML based formats, useful to pass an entire archive to an LLM (`llm archive ... | llm prompt ...`):

- `xml`: XML elements with properly escaped content (e.g., `<foo.html>&lt;em&gt;escaped&lt;/em&gt;</foo.html>`)
- `xmlish`: XML elements with raw content, no escaping (e.g., `<foo.html><em>preserved</em></foo.html>`)

## Workflow Example

Process multiple files in parallel:

```bash
llm archive file1.py file2.js | llm map - "What programming language is this?"
```

Process and extract:

```bash
llm archive file1.py file2.js | llm map - "Add --reticulate-splines option" | llm archive --extract
```

Process multiple files with one call:

```bash
llm archive --format xmlish file1.py file2.js | llm prompt "Is the algorithm identical in both files"
```
