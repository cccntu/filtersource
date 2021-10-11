## Workflow

* Fork this repo & create a new branch
* Add filter code in `src/filters/<dataset_name>/<dataset_config_name>/<rule_name>.py`
    * The file needs to have a `def main(example) -> bool:`
* Commit and create a PR to this repo
    * note: you can try to create PR in your own repo first to test it

Then the github action will do the following:

* Check changed files with correct pattern
* Run the filter function(s) on a fraction of the dataset
* Generate a summary and comment on the PR

Then other language expert can review the code and the summary to determine if it's a good rule, without running the code.
The comment will also serve as a documentation.

