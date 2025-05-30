import argparse
import random
import json
import os
import sys
import time

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
                value = value.strip()
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
    )

def generate_variants(data, use_leet=True, combine_names=True, include_specials="!", prepend="", append="", separator="_", filter_keys=None):
    words = set()
    base = []

    def flatten(val):
        return val if isinstance(val, list) else [val]

    if filter_keys:
        filter_keys = [k.strip().lower() for k in filter_keys.split(',')]
        items = {k: v for k, v in data.items() if k.lower() in filter_keys}.items()
    else:
        items = data.items()

    for key, val in items:
        for v in flatten(val):
            if not v: continue
            base.append(v.lower())
            base.append(v.capitalize())
            if use_leet and v.isalpha():
                base.append(leetspeak(v.lower()))

    first = data.get('first_name', '')
    last = data.get('last_name', '')
    if isinstance(first, list): first = first[0]
    if isinstance(last, list): last = last[0]

    birth_year = data.get('birth_year', '')
    birth_day = data.get('birth_day', '')
    birth_month = data.get('birth_month', '')

    if birth_year:
        base.append(birth_year)
    if birth_day and birth_month:
        base.append(f"{birth_day}{birth_month}")
    if birth_month and birth_year:
        base.append(f"{birth_month}{birth_year}")

    for word in base:
        if not word.strip():
            continue
        w = word.strip()
        words.add(prepend + w + append)
        words.add(prepend + w + "123" + append)
        words.add(prepend + w + "!" + append)
        if birth_year:
            words.add(prepend + w + birth_year + append)
        if len(w) > 3:
            words.add(prepend + w[:3] + "123" + append)

    if combine_names and first and last:
        combos = {
            prepend + first + separator + last + append,
            prepend + last + separator + first + append,
            prepend + first.capitalize() + separator + last.capitalize() + append
        }
        words.update(combos)

    return sorted(words)

def filter_length(words, min_len, max_len):
    return [w for w in words if (min_len is None or len(w) >= min_len) and (max_len is None or len(w) <= max_len)]

def remove_duplicates(words):
    return sorted(set(words))

def remove_common_passwords(words, common_file):
    if not os.path.isfile(common_file):
        print(f"[!] Common passwords file '{common_file}' not found. Skipping removal.")
        return words
    with open(common_file, 'r', encoding='utf-8', errors='ignore') as f:
        common = set(line.strip() for line in f if line.strip())
    return [w for w in words if w not in common]

def combine_passwords(words, max_combinations=10000):
    combined = set()
    length = len(words)
    max_pairs = min(length, int(max_combinations**0.5))
    for i in range(max_pairs):
        for j in range(max_pairs):
            if i == j:
                continue
            combined.add(words[i] + words[j])
            combined.add(words[i] + "_" + words[j])
            if len(combined) >= max_combinations:
                return list(combined)
    return list(combined)

class NoUsageArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self._print_message(f"Error: {message}\n", sys.stderr)
        self.exit(2)

def main():
    parser = NoUsageArgumentParser(description="Smart password wordlist generator.")
    parser.add_argument('-i', '--input', required=True, help='Input file path (e.g., input.txt)')
    parser.add_argument('-o', '--output', default='wordlist.txt', help='Output file (default: wordlist.txt)')
    parser.add_argument('-n', '--num', type=int, help='Max number of passwords')
    parser.add_argument('--no-leet', dest='use_leet', action='store_false', help='Disable leetspeak')
    parser.add_argument('--no-combine', dest='combine_names', action='store_false', help='Disable name combination')
    parser.add_argument('-a', '--append-to', type=str, help='Append to file instead of overwriting')
    parser.add_argument('--min-length', type=int, help='Minimum password length')
    parser.add_argument('--max-length', type=int, help='Maximum password length')
    parser.add_argument('--include-specials', default="!", help='Special characters to append (default: "!")')
    parser.add_argument('--prepend', default="", help='String to prepend to all passwords')
    parser.add_argument('--append-str', default="", help='String to append to all passwords')
    parser.add_argument('--separator', default="_", help='Separator between name parts (default: "_")')
    parser.add_argument('-f', '--filter-keys', help='Comma-separated keys to filter from input')
    parser.add_argument('-s', '--shuffle', action='store_true', help='Shuffle wordlist')
    parser.add_argument('-S', '--stats', action='store_true', help='Show generation statistics')
    parser.add_argument('--export-json', help='Export to JSON instead of text')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Do not write output')
    parser.add_argument('--remove-common', help='File with common passwords to exclude')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('-V', '--verbose-level', type=int, choices=[0, 1, 2], default=1, help='Verbosity (0=silent, 2=debug)')

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.verbose_level >= 1:
        print(f"[+] Reading input from: {args.input}")

    data = parse_input_file(args.input)

    if args.verbose_level >= 1:
        print("[+] Generating password variants...")

    wordlist = generate_variants(
        data,
        use_leet=args.use_leet,
        combine_names=args.combine_names,
        include_specials=args.include_specials,
        prepend=args.prepend,
        append=args.append_str,
        separator=args.separator,
        filter_keys=args.filter_keys
    )

    if args.min_length or args.max_length:
        wordlist = filter_length(wordlist, args.min_length, args.max_length)
        if args.verbose_level >= 2:
            print(f"[DEBUG] Filtered by length: {len(wordlist)} remaining")

    if args.remove_common:
        wordlist = remove_common_passwords(wordlist, args.remove_common)
        if args.verbose_level >= 1:
            print(f"[+] Removed common passwords using {args.remove_common}")

    wordlist = remove_duplicates(wordlist)

    combined = combine_passwords(wordlist, max_combinations=10000)
    wordlist.extend(combined)
    wordlist = remove_duplicates(wordlist)

    if args.shuffle:
        random.shuffle(wordlist)
        if args.verbose_level >= 2:
            print("[DEBUG] Wordlist shuffled")

    if args.num:
        wordlist = wordlist[:args.num]

    if args.dry_run:
        print(f"[+] Dry run enabled: {len(wordlist)} passwords generated (not written)")
    else:
        output_file = args.append_to if args.append_to else args.output
        mode = 'a' if args.append_to else 'w'

        if args.export_json:
            with open(args.export_json, mode, encoding='utf-8') as f:
                json.dump(wordlist, f, indent=2)
            print(f"[+] Wordlist exported to JSON: {args.export_json}")
        else:
            with open(output_file, mode, encoding='utf-8') as f:
                for word in wordlist:
                    f.write(word + '\n')
            print(f"[+] Wordlist saved to {output_file} ({len(wordlist)} entries)")

    if args.stats:
        print("=== Statistics ===")
        print(f"Total: {len(wordlist)}")
        lengths = [len(w) for w in wordlist]
        if lengths:
            print(f"Min: {min(lengths)}")
            print(f"Max: {max(lengths)}")
            print(f"Average: {sum(lengths)/len(lengths):.2f}")

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    print(f"Execution time: {time.perf_counter() - start:.4f} sec")
