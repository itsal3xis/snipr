import random
import argparse
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
    leet_map = {'a':'@', 'e':'3', 'i':'1', 'o':'0', 's':'$', 't':'7'}
    return ''.join(leet_map.get(c, c) for c in word.lower())

def case_variants(word):
    variants = [
        word.lower(),
        word.upper(),
        word.capitalize(),
        ''.join(c.upper() if i%2==0 else c.lower() for i,c in enumerate(word)),
        ''.join(c.lower() if i%2==0 else c.upper() for i,c in enumerate(word)),
        leetspeak(word),
        word[::-1],
    ]
    return list(set(variants))

def generate_variants(words):
    variants_per_word = []
    for w in words:
        variants_per_word.append(case_variants(w))
    return variants_per_word

def random_password_mix(variants_per_word, numbers, specials, separator_list, max_passwords, max_words=6):
    generated = set()
    attempts = 0
    max_passwords = max_passwords
    max_attempts = max_passwords * 10  # Limit attempts to avoid infinite loop
    
    while len(generated) < max_passwords and attempts < max_attempts:
        attempts += 1

        # Choose how many words to combine (1 to max_words)
        num_words = random.randint(1, min(max_words, len(variants_per_word)))

        # Choose random words with replacement (allow repetition for more combos)
        chosen_words = [random.choice(random.choice(variants_per_word)) for _ in range(num_words)]

        # Randomly choose separators between words
        sep = random.choice(separator_list)

        base = sep.join(chosen_words)

        # Add numbers or specials randomly at start/end/inside
        pwds = set()
        pwds.add(base)
        for num in numbers:
            pwds.add(num + base)
            pwds.add(base + num)
            pwds.add(num + base + num)
        for sp in specials:
            pwds.add(sp + base)
            pwds.add(base + sp)
            pwds.add(sp + base + sp)

        # Pick one variant randomly to add to generated
        chosen_pwd = random.choice(list(pwds))
        if chosen_pwd not in generated:
            generated.add(chosen_pwd)

    return list(generated)

def banner():
    banner_text = """  ██████  ███▄    █  ██▓ ██▓███   ██▀███  
▒██    ▒  ██ ▀█   █ ▓██▒▓██░  ██▒▓██ ▒ ██▒
░ ▓██▄   ▓██  ▀█ ██▒▒██▒▓██░ ██▓▒▓██ ░▄█ ▒
  ▒   ██▒▓██▒  ▐▌██▒░██░▒██▄█▓▒ ▒▒██▀▀█▄  
▒██████▒▒▒██░   ▓██░░██░▒██▒ ░  ░░██▓ ▒██▒
▒ ▒▓▒ ▒ ░░ ▒░   ▒ ▒ ░▓  ▒▓▒░ ░  ░░ ▒▓ ░▒▓░
░ ░▒  ░ ░░ ░░   ░ ▒░ ▒ ░░▒ ░       ░▒ ░ ▒░
░  ░  ░     ░   ░ ░  ▒ ░░░         ░░   ░ 
      ░           ░  ░              ░     
                                          """
    print(f"\n\n{banner_text}\nBy itsal3xis\n=============================================\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', default='wordlist.txt')
    parser.add_argument('-n', '--num', type=int, default=100000, help='Max number of passwords to generate')
    parser.add_argument('-m', '--max-length', type=int, default=None, help='Maximum length of passwords')
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    data = parse_input_file(args.input)

    words = []
    for k, v in data.items():
        if k not in ['numbers', 'specials']:
            if isinstance(v, list):
                words.extend(v)
            else:
                words.append(v)

    numbers = data.get('numbers', [])
    if isinstance(numbers, str):
        numbers = [numbers]
    specials = data.get('specials', [])
    if isinstance(specials, str):
        specials = [specials]

    variants_per_word = generate_variants(words)

    separators = ['', '_', '.', '-', '']

    passwords = random_password_mix(variants_per_word, numbers, specials, separators, args.num)


    with open(args.output, 'w', encoding='utf-8') as f:
        for p in passwords:
            if args.max_length is None or len(p) <= args.max_length:
                f.write(p + '\n') 
    if args.max_length is not None:
        banner()
        print(f"Generated {len([p for p in passwords if len(p) <= args.max_length])} passwords with less than {args.max_length} characters\n")
    else:
        banner()
        print(f"\nGenerated {len(passwords)} passwords saved in {args.output}")

if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time() - start
    print(f"Execution took {end:.3f} seconds")
