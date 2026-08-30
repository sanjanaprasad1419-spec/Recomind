def inspect_lines():
    with open('extracted_social_science_raw.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("=================== COURSE OUTLINE LINES 330 to 750 ===================")
    for i in range(330, 750):
        if i < len(lines):
            clean = lines[i].encode('ascii', errors='ignore').decode('ascii').strip()
            if clean:
                print(f"{i+1}: {clean}")

if __name__ == "__main__":
    inspect_lines()
