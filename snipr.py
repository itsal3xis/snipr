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
    return list(set([
        word.lower(),
        word.upper(),
        word.capitalize(),
        ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(word)),
        ''.join(c.lower() if i % 2 == 0 else c.upper() for i, c in enumerate(word))
    ]))

def generate_variants(data, use_leet=True, combine_names=True, include_specials="!@#", prepend="", append="", separator="_", filter_keys=None):
    words = set()
    base_words = []
    numbers = []

    def flatten(val):
        return val if isinstance(val, list) else [val]

    # Filtered keys
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

    # Extend base words with leet and case variants
    extended_words = set()
    for word in base_words:
        extended_words.update(apply_case_variants(word))
        if use_leet:
            extended_words.add(leetspeak(word))
            extended_words.update(apply_case_variants(leetspeak(word)))

    # Generate combinations and permutations up to 3 words
    for r in range(1, 4):
        for combo in itertools.permutations(extended_words, r):
            joined = separator.join(combo)
            words.add(prepend + joined + append)
            for n in numbers:
                words.add(prepend + joined + n + append)
                for special in include_specials:
                    words.add(prepend + joined + special + n + append)
                    words.add(prepend + joined + n + special + append)

    return sorted(words)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input file path')
    parser.add_argument('-o', '--output', default='wordlist.txt', help='Output wordlist')
    parser.add_argument('-n', '--num', type=int, help='Limit number of passwords')
    parser.add_argument('--no-leet', action='store_false', dest='use_leet', help='Disable leetspeak')
    parser.add_argument('--separator', type=str, default='_', help='Separator character')
    parser.add_argument('--prepend', type=str, default='', help='Prepend string')
    parser.add_argument('--append', type=str, default='', help='Append string')
    parser.add_argument('-s', '--specials', type=str, default='!@#', help='Special characters to use')
    parser.add_argument('--filter-keys', type=str, help='Comma-separated keys to include')
    parser.add_argument('--shuffle', action='store_true', help='Shuffle wordlist')
    parser.add_argument('--stats', action='store_true', help='Print stats')
    parser.add_argument('-j', '--json', type=str, help='Export wordlist to JSON')

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