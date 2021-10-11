import argparse
import importlib.util
import json
import sys
from pathlib import Path

from datasets import load_dataset
from git import Repo
from git.objects import commit
from tqdm.auto import tqdm

repo = Repo(__file__, search_parent_directories=True)


def import_file(path):
    # https://stackoverflow.com/a/67692/10214604
    spec = importlib.util.spec_from_file_location("module_name", path)
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return foo


def run_filter(
    dataset_name,
    dataset_config_name,
    filter_fn,
    num_to_save=100,
    min_to_run=1000,
    max_to_run=10_000,
):
    dataset = load_dataset(
        dataset_name, dataset_config_name, streaming=True, split="train"
    )
    filter_fn = module.main
    num_filtered = 0
    filtered = []
    cleaned = []

    for i, example in enumerate(tqdm(dataset.take(max_to_run))):
        good = filter_fn(example)
        if not good:
            num_filtered += 1
            if len(filtered) < num_to_save:
                filtered.append(example)
        elif len(cleaned) < num_to_save:
            cleaned.append(example)
        if num_filtered >= num_to_save and i+1 >= min_to_run:
            break

    num_examples_seen = i + 1
    return (num_filtered, num_examples_seen, filtered, cleaned)


parser = argparse.ArgumentParser()
parser.add_argument("--base_ref", type=str, default="main", help="base commit to diff")
parser.add_argument("--head_ref", type=str, help="commit head")
args = parser.parse_args()

repo_root = repo.working_tree_dir

diff = repo.commit(args.head_ref).diff(args.base_ref)
changed_files = [item.a_path for item in diff]

filter_files = []
for file in changed_files:
    parents = [x.name for x in reversed(Path(file).parents)]
    # ['', 'src', 'filters', 'oscar', 'unshuffled_original_en']
    if len(parents) == 5 and (parents[0], parents[1], parents[2]) == (
        "",
        "src",
        "filters",
    ):
        dataset_name = parents[3]
        dataset_config_name = parents[4]

        path = Path(repo_root, file)
        module = import_file(path)
        if hasattr(module, "main"):
            filter_fn = module.main
            filter_files.append((dataset_name, dataset_config_name, path, filter_fn))
summaries = []
for dataset_name, dataset_config_name, path, filter_fn in filter_files:
    (num_filtered, num_examples_seen, filtered, cleaned) = run_filter(
        dataset_name,
        dataset_config_name,
        filter_fn,
    )

    def truncate_strings(example, len=256):
        return {k: (v[:len] if isinstance(v, str) else v) for k, v in example.items()}

    def truncate_examples(examples, len=256):
        return [truncate_strings(e, len) for e in examples]

    truncate_len = 128
    filtered_truncated = "\n\n".join(
        [
            f"* {str(example)}"
            for example in truncate_examples(filtered[:50], len=truncate_len)
        ]
    )

    cleaned_truncated = "\n\n".join(
        [
            f"* {str(example)}"
            for example in truncate_examples(cleaned[:50], len=truncate_len)
        ]
    )
    summary = f"""
# Summary for {dataset_name}/{dataset_config_name}/{path.name}

## Statistics

* Number of examples seen: {num_examples_seen}
* Number of examples filtered: {num_filtered}
* Percentage of data filtered: {num_filtered/num_examples_seen:.2%}
## Removed examples (texts truncated to {truncate_len})
<details>
<summary>click to expand</summary>

{filtered_truncated}
</details>

## Clean examples (texts truncated to {truncate_len})
<details>
<summary>click to expand</summary>

{cleaned_truncated}
</details>

"""
    summaries.append(summary)
with open("summary.md", "w") as f:
    for summary in summaries:
        f.write(summary)
