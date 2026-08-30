import re

def search():
    with open('extracted_social_science_raw.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.splitlines()
    print(f"Total lines in extracted raw text: {len(lines)}")

    keywords = [
        'part 1', 'part 2', 'shaping of', 'oceans and life', 'understanding social', 
        'atmosphere and climate', 'early humans', 'state and society', 'democracy', 
        'elections', 'building blocks', 'price puzzle', 'life on earth', 
        'resistance and resilience', 'india and the world', 'authority', 
        'ideas to startups', 'manage your finances', 'course outline'
    ]

    for idx, l in enumerate(lines, 1):
        l_lower = l.lower()
        if any(k in l_lower for k in keywords):
            clean_l = l.encode('ascii', errors='ignore').decode('ascii').strip()
            print(f"Line {idx}: {clean_l[:100]}")


if __name__ == "__main__":
    search()
