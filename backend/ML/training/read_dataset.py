import json

with open("../datasets/train-v2.0.json", "r", encoding="utf-8") as file:
    data = json.load(file)

print(data["data"][0]["paragraphs"][0]["context"])