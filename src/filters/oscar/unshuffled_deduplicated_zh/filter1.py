import re


def filter1(text):
    return chr(65533) not in text


def filter2(text):
    """count space and special character"""
    # exclude space around english
    text = re.sub(r" ([a-zA-Z])", r"\g<1>", text)
    text = re.sub(r"([a-zA-Z]) ", r"\g<1>", text)
    # convert some special characters to space
    text = re.sub("[|\n【】]", " ", text)
    space_count = len([c for c in text if c == " "])
    return (space_count / len(text)) < 1 / 10


def main(example) -> bool:
    text = example["text"]
    return filter1(text) and filter2(text)
