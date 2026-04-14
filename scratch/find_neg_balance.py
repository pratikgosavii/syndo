content = open('templates/add_product.html', 'r', encoding='utf-8').read()
balance = 0
for i, char in enumerate(content):
    if char == '{':
        balance += 1
    elif char == '}':
        balance -= 1
    if balance < 0:
        print(f"Negative balance at index {i}: ...{content[i-20:i+1]}...")
        break
else:
    print("No native JS/HTML brace imbalance (or imbalance is only positive).")
