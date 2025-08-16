from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

import llm
import click

from .format import parse_input, output_results


def expand_branches(items: List[dict], branches: int) -> List[dict]:
    """Expand items for branching by duplicating with prefixed paths."""
    if branches == 1:
        return items

    pad_width = len(str(branches - 1))
    expanded = []

    for i in range(branches):
        for item in items:
            expanded_item = item.copy()
            prefix = str(i).zfill(pad_width)
            expanded_item["path"] = f"{prefix}_{item['path']}"
            expanded.append(expanded_item)

    return expanded


def map_items(
    jsonl_file: str,
    prompt_template: str,
    model: str,
    temperature: float,
    tokens: int,
    concurrency: int,
    output: Optional[str],
    branches: int,
    include_input: bool,
    iformat: str,
    oformat: str,
):
    """Apply LLM prompt to items."""
    items = parse_input(jsonl_file, iformat)
    expanded_items = expand_branches(items, branches)
    results = []

    def process_item(item):
        try:
            content = item.get("content", "")
            path = item.get("path", "")

            if not prompt_template:
                formatted_prompt = content
            elif "{item}" in prompt_template:
                formatted_prompt = prompt_template.replace("{item}", content, 1)
            else:
                formatted_prompt = f"{prompt_template}\n{content}"

            model_obj = llm.get_model(model)
            response = model_obj.prompt(
                formatted_prompt, temperature=temperature, max_tokens=tokens
            )

            result = {"path": path, "content": response.text()}

            if include_input:
                result["input"] = content

            return result
        except Exception as e:
            result = {"path": item.get("path", ""), "error": str(e)}
            if include_input:
                result["input"] = item.get("content", "")
            return result

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_item = {
            executor.submit(process_item, item): item for item in expanded_items
        }

        show_progress = sys.stderr.isatty()
        if show_progress:
            with click.progressbar(
                length=len(expanded_items), label="Processing items", file=sys.stderr
            ) as bar:
                for future in as_completed(future_to_item):
                    result = future.result()
                    results.append(result)
                    bar.update(1)
        else:
            for future in as_completed(future_to_item):
                result = future.result()
                results.append(result)

    output_results(results, output, oformat)
