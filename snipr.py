import argparse
import random
import json
import os
import sys
import time
import itertools

def parse_input_file(file_path):
    data = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # skip comments and blank lines
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                # Remove spaces inside values (your request)
                value = value.replace(' ', '')
                if key in data:
                    if isinstance(data[key], list):
                        data[key].append(value)
                    else:
                        data[key] = [data[key], value]
                else:
                    data[key] = value
    return data

def leetspeak(word):
    leet_map = {'a':'@', 'e':'3', 'i':'1', 'o':'0', 's':'$', 't':'7'}
    return ''.join(leet_map.get(c, c) for c in word.lower())

def case_variants(word):
    return list(set([
        word.lower(),
        word.upper(),
        word.capitalize(),
        ''.join(c.upper() if i % 2 == 0 else c.lower() for i,c in enumerate(word)),
        ''.join(c.lower() if i % 2 == 0 else c.upper() for i,c in enumerate(word)),
        leetspeak(word),
        word[::-1],  # reversed
    ]))

def generate_variants_for_words(words, use_leet=True):
    variants_per_word = []
    for w in words:
        w = w.strip()
        if not w:
            continue
        variants = case_variants(w)
        if use_leet:
            variants.append(leetspeak(w))
        # Remove duplicates
        variants = list(set(variants))
        variants_per_word.append(variants)
    return variants_per_word

def combine_all_variants(variants_per_word, numbers, specials, separator='_', max_length=None, max_passwords=None):
    all_passwords = set()
    max_words_in_combination = min(4, len(variants_per_word))  # max 4 words combined
    
    # Helper to add numbers and specials at start/end/middle
    def add_numbers_specials(pwd):
        combos = set()
        combos.add(pwd)
        for num in numbers:
            combos.add(num + pwd)
            combos.add(pwd + num)
            combos.add(num + pwd + num)
        for sp in specials:
            combos.add(sp + pwd)
            combos.add(pwd + sp)
            combos.add(sp + pwd + sp)
        return combos

    for r in range(1, max_words_in_combination + 1):
        # All combinations of words (without order)
        for combo_words in itertools.combinations(variants_per_word, r):
            # For each combination, generate all permutations (to mix order)
            for permuted_words in itertools.permutations(combo_words):
                # permuted_words is tuple of lists of variants per word
                # We want to pick one variant from each word's variants:
                for variant_combo in itertools.product(*permuted_words):
                    # Combine with separator or no separator
                    base_variants = [
                        ''.join(variant_combo),
                        separator.join(variant_combo),
                    ]
                    # For each base variant, add numbers and specials combos
                    for base in base_variants:
                        if max_length and len(base) > max_length:
                            continue
                        extended_pwds = add_numbers_specials(base)
                        for pwd in extended_pwds:
                            if max_length and len(pwd) > max_length:
                                continue
                            all_passwords.add(pwd)
                            if max_passwords and len(all_passwords) >= max_passwords:
                                return list(all_passwords)
    return list(all_passwords)

def main():
    parser = argparse.ArgumentParser(description="Extensive smart password wordlist generator.")
    parser.add_argument('-i', '--input', required=True, help='Input file path')
    parser.add_argument('-o', '--output', default='wordlist.txt', help='Output wordlist file')
    parser.add_argument('-n', '--num', type=int, default=None, help='Max number of passwords to generate')
    parser.add_argument('--no-leet', action='store_false', dest='use_leet', help='Disable leetspeak transformations')
    parser.add_argument('--separator', default='_', help='Separator to join words')
    parser.add_argument('--specials', default='!@#', help='Special chars to add around passwords')
    parser.add_argument('--min-length', type=int, default=None, help='Minimum length of passwords')
    parser.add_argument('--max-length', type=int, default=None, help='Maximum length of passwords')
    parser.add_argument('--dry-run', action='store_true', help='Do not write output file')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)

    data = parse_input_file(args.input)

    # Extract words to variants - use all keys except numbers and specials
    word_keys = [k for k in data.keys() if k not in ['birth_year', 'birth_day', 'birth_month', 'numbers', 'specials']]
    words = []
    for k in word_keys:
        val = data[k]
        if isinstance(val, list):
            words.extend(val)
        else:
            words.append(val)

    # Numbers from file
    numbers = []
    if 'numbers' in data:
        if isinstance(data['numbers'], list):
            numbers = data['numbers']
        else:
            numbers = [data['numbers']]
    else:
        # fallback: empty or just some basic numbers
        numbers = []

    # Specials from input or args
    specials = list(args.specials)
    if 'specials' in data:
        if isinstance(data['specials'], list):
            specials.extend(data['specials'])
        else:
            specials.append(data['specials'])
    specials = list(set(specials))  # unique

    variants_per_word = generate_variants_for_words(words, use_leet=args.use_leet)

    passwords = combine_all_variants(
        variants_per_word,
        numbers=numbers,
        specials=specials,
        separator=args.separator,
        max_length=args.max_length,
        max_passwords=args.num,
    )

    if args.min_length:
        passwords = [p for p in passwords if len(p) >= args.min_length]

    if args.num:
        passwords = passwords[:args.num]

    if args.dry_run:
        print(f"[+] Dry run: generated {len(passwords)} passwords, not saving.")
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            for p in passwords:
                f.write(p + '\n')
        print(f"[+] Generated {len(passwords)} passwords saved to {args.output}")

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    print(f"Execution time: {end - start:.4f} seconds")
