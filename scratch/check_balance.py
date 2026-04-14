import re

def check_balance(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    pairs = [
        ('{%', '%}'),
        ('{{', '}}'),
        ('{', '}'),
        ('[', ']'),
        ('(', ')'),
    ]

    for open_tag, close_tag in pairs:
        open_count = content.count(open_tag)
        close_count = content.count(close_tag)
        if open_count != close_count:
            print(f"IMBALANCE: '{open_tag}'={open_count}, '{close_tag}'={close_count}")
        else:
            print(f"Balanced: '{open_tag}'/'{close_tag}' ({open_count})")

if __name__ == "__main__":
    check_balance(r"c:\Users\Pratik Gosavi\OneDrive\Desktop\hope again\syndo\templates\add_product.html")
