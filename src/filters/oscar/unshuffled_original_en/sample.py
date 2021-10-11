def main(example):
    text = example["text"]
    if len(text) < 128:
        return False
    return True
