import argparse
import random
import json
import os
import platform
import sys
import time
import itertools

def parse_input_file(file_path):
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip().replace(' ', '')
                if key in data:
                    if isinstance(data[key], list):
                        data[key].append(value)
                    else:
                        data[key] = [data[key], value]
                else:
                    data[key] = value
    return data

def leetspeak(word):
    return (
        word.replace('a', '@')
            .replace('e', '3')
            .replace('i', '1')
            .replace('o', '0')
            .replace('s', '$')
            .replace('t', '7')
            .replace('b', '8')
    )

def apply_case_variants(word):
    variants = set()
    variants.add(word.lower())
    variants.add(word.upper())
    variants.add(word.capitalize())
    variants.add(''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(word)))
    variants.add(''.join(c.lower() if i % 2 == 0 else c.upper() for i, c in enumerate(word)))
    return variants

def generate_variants(data, use_leet=True, combine_names=True, include_specials="!@#", prepend="", append="", separator="_", filter_keys=None):
    words = set()
    base_words = []
    numbers = []

    def flatten(val):
        return val if isinstance(val, list) else [val]

    items = data.items()
    if filter_keys:
        filter_keys = [k.strip().lower() for k in filter_keys.split(',')]
        items = [(k, v) for k, v in data.items() if k.lower() in filter_keys]

    for key, val in items:
        for v in flatten(val):
            clean = v.strip().replace(' ', '')
            if clean.isdigit():
                numbers.append(clean)
            else:
                base_words.append(clean)

    extended_words = set()
    for word in base_words:
        extended_words.update(apply_case_variants(word))
        if use_leet:
            leet_word = leetspeak(word)
            extended_words.add(leet_word)
            extended_words.update(apply_case_variants(leet_word))

    all_combos = set()
    for r in range(1, 5):
        for combo in itertools.permutations(extended_words, r):
            base = separator.join(combo)
            all_combos.add(base)

    final_words = set()
    for combo in all_combos:
        final_words.add(prepend + combo + append)
        for number in numbers:
            final_words.add(prepend + combo + number + append)
            final_words.add(prepend + number + combo + append)
            for special in include_specials:
                final_words.add(prepend + combo + special + number + append)
                final_words.add(prepend + number + combo + special + append)
                final_words.add(prepend + special + combo + number + append)
                final_words.add(prepend + combo + number + special + append)
                final_words.add(prepend + number + special + combo + append)

    return sorted(final_words)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input file path')
    parser.add_argument('-o', '--output', default='wordlist.txt', help='Output wordlist')
    parser.add_argument('-n', '--num', type=int, help='Limit number of passwords')
    parser.add_argument('--no-leet', action='store_false', dest='use_leet', help='Disable leetspeak')
    parser.add_argument('--separator', type=str, default='_', help='Separator character')
    parser.add_argument('--prepend', type=str, default='', help='Prepend string')
    parser.add_argument('--append', type=str, default='', help='Append string')
    parser.add_argument('--specials', type=str, default='!@#', help='Special characters to use')
    parser.add_argument('--filter-keys', type=str, help='Comma-separated keys to include')
    parser.add_argument('--shuffle', action='store_true', help='Shuffle wordlist')
    parser.add_argument('--stats', action='store_true', help='Print stats')
    parser.add_argument('--json', type=str, help='Export wordlist to JSON')

    args = parser.parse_args()

    start = time.perf_counter()
    data = parse_input_file(args.input)

    wordlist = generate_variants(
        data,
        use_leet=args.use_leet,
        include_specials=args.specials,
        prepend=args.prepend,
        append=args.append,
        separator=args.separator,
        filter_keys=args.filter_keys
    )

    if args.shuffle:
        random.shuffle(wordlist)

    if args.num:
        wordlist = wordlist[:args.num]

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(wordlist, f, indent=2)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(wordlist))

    if args.stats:
        print("=== Stats ===")
        print(f"Total passwords: {len(wordlist)}")
        lengths = [len(w) for w in wordlist]
        print(f"Min length: {min(lengths)}")
        print(f"Max length: {max(lengths)}")
        print(f"Average length: {sum(lengths)/len(lengths):.2f}")

    print(f"Execution time: {time.perf_counter() - start:.4f} seconds")

if __name__ == '__main__':
    main()
