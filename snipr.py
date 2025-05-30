import argparse
import random
import json
import os
import platform
import sys
import time

def parse_input_file(file_path):
    data = {}
    with open(file_path, 'r') as f:
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

def sanitize_value(val, replace_with=""):
    return val.replace(" ", replace_with)

def apply_case(word, case_option):
    if case_option == 'lower':
        return word.lower()
    elif case_option == 'upper':
        return word.upper()
    elif case_option == 'capitalize':
        return word.capitalize()
    elif case_option == 'mixed':
        return ''.join(c.upper() if random.choice([True, False]) else c.lower() for c in word)
    else:
        return word

def generate_variants(data, use_leet=True, combine_names=True, include_specials="!", prepend="", append="", separator="_", filter_keys=None):
    words = set()
    base = []

    def flatten_value(val):
        return val if isinstance(val, list) else [val]

    items = data.items()
    if filter_keys:
        filter_keys = [k.strip().lower() for k in filter_keys.split(',')]
        items = [(k, v) for k, v in data.items() if k.lower() in filter_keys]

    for key, val in items:
        for v in flatten_value(val):
            if v:
                clean = sanitize_value(v)
                base.append(clean.lower())
                base.append(clean.capitalize())
                if use_leet and clean.isalpha():
                    base.append(leetspeak(clean.lower()))

    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    if isinstance(first_name, list):
        first_name = first_name[0]
    if isinstance(last_name, list):
        last_name = last_name[0]

    birth_year = data.get('birth_year', '')
    birth_day = data.get('birth_day', '')
    birth_month = data.get('birth_month', '')

    if birth_year:
        base.append(birth_year)
    if birth_day and birth_month:
        base.append(f"{birth_day}{birth_month}")
    if birth_month and birth_year:
        base.append(f"{birth_month}{birth_year}")

    for w in base:
        if not w:
            continue
        w = w.strip()
        words.add(prepend + w + append)
        words.add(prepend + w + "123" + append)
        words.add(prepend + w + "!" + append)
        if birth_year:
            words.add(prepend + w + birth_year + append)
        if len(w) > 3:
            words.add(prepend + w[:3] + "123" + append)

    if combine_names and first_name and last_name:
        first_name = sanitize_value(first_name)
        last_name = sanitize_value(last_name)
        combo1 = prepend + first_name + separator + last_name + append
        combo2 = prepend + last_name + separator + first_name + append
        combo3 = prepend + first_name.capitalize() + separator + last_name.capitalize() + append
        words.update({combo1, combo2, combo3})

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
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', default='wordlist.txt')
    parser.add_argument('-n', '--num', type=int)
    parser.add_argument('--no-leet', action='store_false', dest='use_leet')
    parser.add_argument('--no-combine', action='store_false', dest='combine_names')
    parser.add_argument('-a', '--append-to')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--min-length', type=int)
    parser.add_argument('--max-length', type=int)
    parser.add_argument('--include-specials', type=str, default="!")
    parser.add_argument('--prepend', type=str, default="")
    parser.add_argument('--append-str', type=str, default="")
    parser.add_argument('--separator', type=str, default="_")
    parser.add_argument('-f', '--filter-keys')
    parser.add_argument('-s', '--shuffle', action='store_true')
    parser.add_argument('-S', '--stats', action='store_true')
    parser.add_argument('--export-json')
    parser.add_argument('-d', '--dry-run', action='store_true')
    parser.add_argument('--remove-common')
    parser.add_argument('--seed', type=int)
    parser.add_argument('-V', '--verbose-level', type=int, choices=[0,1,2], default=1)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.verbose_level >= 1:
        print(f"[+] Reading input from {args.input}...")

    data = parse_input_file(args.input)

    if args.verbose_level >= 1:
        print("[+] Generating wordlist...")

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
            print(f"[DEBUG] Filtered by length: {len(wordlist)} words remain")

    if args.remove_common:
        wordlist = remove_common_passwords(wordlist, args.remove_common)
        if args.verbose_level >= 1:
            print(f"[+] Removed common passwords from {args.remove_common}")

    wordlist = remove_duplicates(wordlist)
    combined_pairs = combine_passwords(wordlist, max_combinations=10000)
    wordlist.extend(combined_pairs)
    wordlist = remove_duplicates(wordlist)

    if args.shuffle:
        random.shuffle(wordlist)
        if args.verbose_level >= 2:
            print("[DEBUG] Shuffled the wordlist")

    if args.num:
        wordlist = wordlist[:args.num]

    if args.dry_run:
        if args.verbose_level >= 1:
            print(f"[+] Dry run enabled. Would generate {len(wordlist)} passwords. Not writing to file.")
    else:
        output_file = args.append_to if args.append_to else args.output
        mode = 'a' if args.append_to else 'w'

        if args.export_json:
            with open(args.export_json, mode) as f:
                json.dump(wordlist, f, indent=2)
            if args.verbose_level >= 1:
                print(f"[+] Exported wordlist to JSON file {args.export_json}")
        else:
            with open(output_file, mode, encoding='utf-8') as f:
                for word in wordlist:
                    f.write(word + '\n')
                if args.verbose_level == 2:
                    print(f"[DEBUG] {word}")
            if args.verbose_level >= 1:
                print(f"[+] Wordlist saved to {output_file} ({len(wordlist)} passwords)")

    if args.stats:
        print("=== Statistics ===")
        print(f"Total passwords generated: {len(wordlist)}")
        lengths = [len(w) for w in wordlist]
        if lengths:
            print(f"Min length: {min(lengths)}")
            print(f"Max length: {max(lengths)}")
            avg_len = sum(lengths) / len(lengths)
            print(f"Average length: {avg_len:.2f}")

if __name__ == "__main__":
    start_time = time.perf_counter()
    main()
    duration = time.perf_counter() - start_time
    print(f"Execution time: {duration:.6f} seconds")
