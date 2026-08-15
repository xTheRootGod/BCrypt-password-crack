#!/usr/bin/env python3

import sys
import os
import time
import math
import string
import shutil
import itertools
from concurrent.futures import ProcessPoolExecutor
import bcrypt


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    OKCYAN = '\033[96m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


HIDE_CURSOR = '\033[?25l'
SHOW_CURSOR = '\033[?25h'


def center_text(text):
    width = shutil.get_terminal_size((80, 20)).columns
    lines = text.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    pad = max((width - max_len) // 2, 0)
    return '\n'.join(' ' * pad + line for line in lines)


def logo():
    art = r'''                _
               /`_>
              / /
              |/
          ____|    __
         |    \.-``  )
         |---``\  _.'
      .-`'---``_.'
     (__...--``    BCrypt crack 2.0 Final Release
                             By TheRootGod
                             
                             tryhackme.com/p/TheRootGod
                             github.com/xTheRootGod
                             
'''
    print(bcolors.WARNING + center_text(art) + bcolors.ENDC)


def attack_tree():
    tree = r'''
   |
   +-- Dictionary
   +-- Rules
   +-- Masks
   +-- Hybrid
   +-- Brute force
   +-- GPU acceleration
             |
             v
        bcrypt hashes
'''
    print(bcolors.OKCYAN + center_text(tree) + bcolors.ENDC)


def is_valid_bcrypt_hash(h):
    if not h.startswith(('$2a$', '$2b$', '$2x$', '$2y$')):
        return False
    parts = h.split('$')
    if len(parts) != 4:
        return False
    cost, salt_and_hash = parts[2], parts[3]
    if not cost.isdigit():
        return False
    if len(salt_and_hash) != 53:
        return False
    return True


def load_wordlist(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        words = [line.rstrip('\n').rstrip('\r') for line in f]
    return [w for w in words if w]


def r_identity(w):
    return w


def r_capitalize(w):
    return w.capitalize()


def r_upper(w):
    return w.upper()


def r_lower(w):
    return w.lower()


def r_reverse(w):
    return w[::-1]


def r_leet(w):
    table = str.maketrans({'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5'})
    return w.translate(table)


def r_append_123(w):
    return w + "123"


def r_append_1234(w):
    return w + "1234"


def r_append_bang(w):
    return w + "!"


def r_append_year(w):
    return w + "2026"


def r_prepend_1(w):
    return "1" + w


RULES = [r_identity, r_capitalize, r_upper, r_lower, r_reverse,
         r_leet, r_append_123, r_append_1234, r_append_bang,
         r_append_year, r_prepend_1]

MASK_CHARSETS = {
    'l': string.ascii_lowercase,
    'u': string.ascii_uppercase,
    'd': string.digits,
    's': "!@#$%^&*()-_=+[]{};:,.<>?/",
    'a': string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.<>?/",
}


def parse_mask(mask):
    charsets = []
    i = 0
    while i < len(mask):
        if mask[i] == '?' and i + 1 < len(mask) and mask[i + 1] in MASK_CHARSETS:
            charsets.append(MASK_CHARSETS[mask[i + 1]])
            i += 2
        else:
            charsets.append(mask[i])
            i += 1
    return charsets


def mask_keyspace(charsets):
    return math.prod(len(c) for c in charsets) if charsets else 0


def generate_dictionary(words):
    for w in words:
        yield w


def dictionary_keyspace(words):
    return len(words)


def generate_rules(words, rules=RULES):
    for w in words:
        for fn in rules:
            yield fn(w)


def rules_keyspace(words, rules=RULES):
    return len(words) * len(rules)


def generate_mask(mask):
    charsets = parse_mask(mask)
    for combo in itertools.product(*charsets):
        yield ''.join(combo)


def generate_hybrid(words, mask, order='append'):
    charsets = parse_mask(mask)
    for w in words:
        for combo in itertools.product(*charsets):
            suffix = ''.join(combo)
            yield (w + suffix) if order == 'append' else (suffix + w)


def hybrid_keyspace(words, charsets):
    return len(words) * mask_keyspace(charsets)


def generate_bruteforce(charset, min_len, max_len):
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(charset, repeat=length):
            yield ''.join(combo)


def bruteforce_keyspace(charset_len, min_len, max_len):
    return sum(charset_len ** length for length in range(min_len, max_len + 1))


def format_count(n):
    if n < 1_000_000:
        return f"{n:,}"
    digits = len(str(n))
    if digits <= 15:
        return f"{n:.3e}"
    mantissa_str = str(n)[:4]
    mantissa = f"{mantissa_str[0]}.{mantissa_str[1:]}"
    exponent = digits - 1
    return f"{mantissa}e+{exponent}"


def format_eta(seconds):
    if seconds is None or seconds == float('inf'):
        return "--:--:--"
    try:
        seconds = int(seconds)
    except (OverflowError, ValueError):
        return ">999h"
    if seconds > 999 * 3600:
        return ">999h"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def safe_eta(total, rate):
    if not total or rate <= 0:
        return None
    try:
        return total / rate
    except OverflowError:
        return float('inf')


def check_candidate(args):
    password, hash_bytes = args
    try:
        matched = bcrypt.checkpw(password.encode('utf-8', errors='ignore'), hash_bytes)
        return (password, matched)
    except Exception:
        return (password, False)


def benchmark_rate(hash_bytes):
    start = time.time()
    bcrypt.checkpw(b"benchmark_sample_password", hash_bytes)
    elapsed = time.time() - start
    return 1.0 / elapsed if elapsed > 0 else 1.0


def draw_panel(hash_input, mode, total, attempted, current_password, rate, elapsed, eta, workers, status="RUNNING", found_password=None):
    width = shutil.get_terminal_size((80, 20)).columns
    box_width = min(max(width - 4, 50), 78)
    inner = box_width - 2

    def line(content, color=bcolors.OKCYAN):
        pad = inner - len(content)
        if pad < 0:
            content = content[:inner]
            pad = 0
        return color + "│" + content + " " * pad + "│" + bcolors.ENDC

    top = bcolors.OKCYAN + "┌" + "─" * inner + "┐" + bcolors.ENDC
    sep = bcolors.OKCYAN + "├" + "─" * inner + "┤" + bcolors.ENDC
    bot = bcolors.OKCYAN + "└" + "─" * inner + "┘" + bcolors.ENDC

    title = " BCRYPT CRACK 2.0 ".center(inner, "─")
    title_line = bcolors.OKCYAN + "├" + bcolors.BOLD + bcolors.OKGREEN + title + bcolors.ENDC + bcolors.OKCYAN + "┤" + bcolors.ENDC

    total_display = format_count(total) if total else "?"
    pct = (attempted / total * 100) if total else 0
    bar_width = max(inner - 18, 10)
    filled = int(bar_width * attempted / total) if total else 0
    filled = min(filled, bar_width)
    bar = "█" * filled + bcolors.DIM + "░" * (bar_width - filled) + bcolors.ENDC + bcolors.OKCYAN

    rows = [top, title_line, sep]
    rows.append(line(f" Hash      : {hash_input[:inner - 13]}"))
    rows.append(line(f" Mode      : {mode}"))
    rows.append(line(f" Status    : {status}", bcolors.OKGREEN if status == "RUNNING" else bcolors.FAIL))
    rows.append(line(f" Workers   : {workers}"))
    rows.append(sep)
    rows.append(line(f" Tried     : {attempted:,} / {total_display}  ({pct:5.1f}%)"))
    rows.append(line(f" Speed     : {rate:,.1f} pw/s"))
    rows.append(line(f" Elapsed   : {format_eta(elapsed)}   ETA: {format_eta(eta)}"))
    rows.append(line(f" Current   : {current_password[:inner - 13]}"))
    rows.append(sep)
    bar_line_content = " " * max(inner - bar_width - 7, 0) + f" {pct:5.1f}%"
    rows.append(bcolors.OKCYAN + "│" + bar + bar_line_content + bcolors.OKCYAN + "│" + bcolors.ENDC)
    rows.append(bot)

    if found_password is not None:
        rows.append("")
        rows.append(bcolors.OKGREEN + bcolors.BOLD + f"  [+] KEY FOUND: {found_password}" + bcolors.ENDC)

    return "\n".join(rows)


def display_password_details(password, hash_input):
    print(bcolors.OKBLUE + "| Password Details:")
    print(bcolors.OKBLUE + f"|   Length: {len(password)}")
    print(bcolors.OKBLUE + f"|   Characters: {' '.join(password)}")
    print(bcolors.OKBLUE + f"|   ASCII Values: {' '.join(str(ord(c)) for c in password)}")
    print(bcolors.OKBLUE + f"|   Hashed Password: {hash_input}")


def run_attack(hash_input, hash_bytes, mode, candidate_gen, total, max_workers):
    found_password = None
    attempted = 0
    start_time = time.time()
    panel_lines = 0
    window = max_workers * 4

    print(HIDE_CURSOR, end='')
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            pending = {}
            exhausted = False

            def fill_window():
                nonlocal exhausted
                while len(pending) < window and not exhausted:
                    try:
                        candidate = next(candidate_gen)
                    except StopIteration:
                        exhausted = True
                        break
                    fut = executor.submit(check_candidate, (candidate, hash_bytes))
                    pending[fut] = candidate

            fill_window()
            last_draw = 0

            while pending:
                done_fut = None
                for fut in list(pending.keys()):
                    if fut.done():
                        done_fut = fut
                        break
                if done_fut is None:
                    time.sleep(0.01)
                    continue

                password = pending.pop(done_fut)
                _, matched = done_fut.result()
                attempted += 1

                now = time.time()
                if matched or now - last_draw > 0.1:
                    last_draw = now
                    elapsed = now - start_time
                    rate = attempted / elapsed if elapsed > 0 else 0
                    eta = None
                    if total and rate > 0:
                        remaining = max(total - attempted, 0)
                        eta = safe_eta(remaining, rate)

                    panel = draw_panel(
                        hash_input, mode, total, attempted, password, rate,
                        elapsed, eta, max_workers,
                        status="RUNNING",
                        found_password=password if matched else None
                    )
                    if panel_lines:
                        sys.stdout.write(f"\033[{panel_lines}F")
                    sys.stdout.write(panel + "\n")
                    sys.stdout.flush()
                    panel_lines = panel.count("\n") + 1

                if matched:
                    found_password = password
                    for f in list(pending.keys()):
                        f.cancel()
                    break

                fill_window()

    except KeyboardInterrupt:
        print(SHOW_CURSOR, end='')
        print(bcolors.WARNING + "\n| Interrupted by user (Ctrl+C). Exiting cleanly." + bcolors.ENDC)
        sys.exit(130)

    print(SHOW_CURSOR, end='')
    print()
    return found_password


def menu_select_mode():
    print(bcolors.OKCYAN + bcolors.BOLD + "Select attack mode:" + bcolors.ENDC)
    options = [
        ("1", "Dictionary"),
        ("2", "Rules (dictionary + mutations)"),
        ("3", "Mask"),
        ("4", "Hybrid (dictionary + mask)"),
        ("5", "Brute force"),
        ("6", "GPU acceleration (info)"),
    ]
    for key, label in options:
        print(f"  [{key}] {label}")
    choice = input("Mode > ").strip()
    return choice


def main():
    logo()

    hash_input = input("Hash > ").strip()

    if not is_valid_bcrypt_hash(hash_input):
        print(bcolors.FAIL + "| The provided hash does not look like a valid bcrypt hash "
              "(must start with $2a$, $2b$, $2x$ or $2y$)." + bcolors.ENDC)
        sys.exit(1)

    hash_bytes = hash_input.encode('utf-8')

    try:
        max_workers = max(1, (os.cpu_count() or 2) - 1)
    except Exception:
        max_workers = 1

    choice = menu_select_mode()

    mode_name = None
    candidate_gen = None
    total = None

    if choice == "1":
        mode_name = "Dictionary"
        passl = input("Wordlist path > ").strip()
        if not os.path.exists(passl):
            print(bcolors.FAIL + "| Couldn't find the required list!" + bcolors.ENDC)
            sys.exit(1)
        words = load_wordlist(passl)
        if not words:
            print(bcolors.FAIL + "| The wordlist is empty!" + bcolors.ENDC)
            sys.exit(1)
        total = dictionary_keyspace(words)
        candidate_gen = generate_dictionary(words)

    elif choice == "2":
        mode_name = "Rules"
        passl = input("Wordlist path > ").strip()
        if not os.path.exists(passl):
            print(bcolors.FAIL + "| Couldn't find the required list!" + bcolors.ENDC)
            sys.exit(1)
        words = load_wordlist(passl)
        if not words:
            print(bcolors.FAIL + "| The wordlist is empty!" + bcolors.ENDC)
            sys.exit(1)
        total = rules_keyspace(words)
        candidate_gen = generate_rules(words)
        print(bcolors.OKBLUE + f"| {len(RULES)} mutation rules will be applied per word "
              f"(capitalize, leetspeak, append digits/year, reverse, etc.)" + bcolors.ENDC)

    elif choice == "3":
        mode_name = "Mask"
        print(bcolors.OKBLUE + "| Mask syntax: ?l lowercase  ?u uppercase  ?d digit  ?s special  ?a all"
              "\n| Example: ?u?l?l?l?d?d?d?d  ->  Aaaa1234" + bcolors.ENDC)
        mask = input("Mask > ").strip()
        charsets = parse_mask(mask)
        if not charsets:
            print(bcolors.FAIL + "| Invalid or empty mask!" + bcolors.ENDC)
            sys.exit(1)
        total = mask_keyspace(charsets)
        candidate_gen = generate_mask(mask)

    elif choice == "4":
        mode_name = "Hybrid"
        passl = input("Wordlist path > ").strip()
        if not os.path.exists(passl):
            print(bcolors.FAIL + "| Couldn't find the required list!" + bcolors.ENDC)
            sys.exit(1)
        words = load_wordlist(passl)
        if not words:
            print(bcolors.FAIL + "| The wordlist is empty!" + bcolors.ENDC)
            sys.exit(1)
        print(bcolors.OKBLUE + "| Mask syntax: ?l lowercase  ?u uppercase  ?d digit  ?s special  ?a all"
              "\n| Example: ?d?d?d?d  ->  appends 4 digits to each word" + bcolors.ENDC)
        mask = input("Mask > ").strip()
        order = input("Attach mask as [append/prepend] (default append) > ").strip().lower() or "append"
        charsets = parse_mask(mask)
        if not charsets:
            print(bcolors.FAIL + "| Invalid or empty mask!" + bcolors.ENDC)
            sys.exit(1)
        total = hybrid_keyspace(words, charsets)
        candidate_gen = generate_hybrid(words, mask, order=order)

    elif choice == "5":
        mode_name = "Brute force"
        print(bcolors.OKBLUE + "| Charset options: l=lowercase u=uppercase d=digits s=special a=all"
              "\n| Example: ld  ->  lowercase letters + digits"
              "\n| Press Enter or 0 on any prompt below to use the default (try everything)."
              + bcolors.ENDC)
        charset_choice = input("Charset (combine letters, e.g. ld) [default: a = all] > ").strip().lower()
        if charset_choice in ("", "0"):
            charset_choice = "a"
        charset = ""
        for c in charset_choice:
            if c in MASK_CHARSETS and c != 'a':
                charset += MASK_CHARSETS[c]
        if not charset:
            charset = MASK_CHARSETS['a']
        charset = ''.join(sorted(set(charset)))

        min_len_raw = input("Min length [default: 1] > ").strip()
        max_len_raw = input("Max length [default: 6] > ").strip()

        try:
            min_len = 1 if min_len_raw in ("", "0") else int(min_len_raw)
            max_len = 6 if max_len_raw in ("", "0") else int(max_len_raw)
        except ValueError:
            print(bcolors.FAIL + "| Invalid length!" + bcolors.ENDC)
            sys.exit(1)

        if min_len < 1 or max_len < min_len:
            print(bcolors.FAIL + "| Invalid length range!" + bcolors.ENDC)
            sys.exit(1)

        total = bruteforce_keyspace(len(charset), min_len, max_len)
        rate_guess = benchmark_rate(hash_bytes) * max_workers
        eta_guess = safe_eta(total, rate_guess)

        print(bcolors.WARNING + f"| Keyspace: {format_count(total)} candidates"
              f"\n| Estimated time at ~{rate_guess:.1f} pw/s (rough, {max_workers} workers): "
              f"{format_eta(eta_guess)}" + bcolors.ENDC)
        if total.bit_length() > 200:
            print(bcolors.FAIL + "| Warning: this keyspace is astronomically large "
                  "(more candidates than atoms in the observable universe, "
                  "in some cases). This is not practically crackable - "
                  "consider a much smaller length range or a smaller charset."
                  + bcolors.ENDC)
        confirm = input("Proceed? [y/N] > ").strip().lower()
        if confirm != 'y':
            print(bcolors.WARNING + "| Cancelled." + bcolors.ENDC)
            sys.exit(0)

        candidate_gen = generate_bruteforce(charset, min_len, max_len)

    elif choice == "6":
        print(bcolors.WARNING + "| GPU acceleration note:" + bcolors.ENDC)
        print(bcolors.WARNING +
              "| bcrypt's cost factor is deliberately designed to resist GPU/ASIC speedup\n"
              "| (unlike MD5/SHA1/NTLM). A real GPU implementation needs hand-written\n"
              "| OpenCL/CUDA kernels, similar to hashcat's mode -m 3200. That is not\n"
              "| something this Python tool can safely or honestly reimplement.\n"
              "| For genuine GPU-accelerated bcrypt cracking, use hashcat (-m 3200)\n"
              "| or John the Ripper with an OpenCL build, and cite that in your report.\n"
              "| This tool maximizes CPU parallelism instead (multi-core, all modes above)."
              + bcolors.ENDC)
        sys.exit(0)

    else:
        print(bcolors.FAIL + "| Invalid selection!" + bcolors.ENDC)
        sys.exit(1)

    print(bcolors.OKBLUE + "+---------------------------------------+")
    print(bcolors.OKBLUE + f"| Mode: {mode_name}")
    print(bcolors.OKBLUE + f"| Keyspace: {format_count(total) if total else 'unbounded'}")
    print(bcolors.OKBLUE + f"| Using {max_workers} worker process(es)")
    print(bcolors.OKBLUE + "+---------------------------------------+" + bcolors.ENDC)

    found_password = run_attack(hash_input, hash_bytes, mode_name, candidate_gen, total, max_workers)

    if found_password is not None:
        print(bcolors.OKGREEN + "+---------------------------------------+")
        print(bcolors.OKGREEN + "| Operation completed successfully!")
        print(bcolors.OKGREEN + "| HASH >    " + hash_input)
        print(bcolors.OKGREEN + "| Password >" + " " + found_password)
        print(bcolors.OKGREEN + "+---------------------------------------+" + bcolors.ENDC)
        display_password_details(found_password, hash_input)
        sys.exit(0)
    else:
        print(bcolors.FAIL + "| Password not found. Try another mode or wordlist." + bcolors.ENDC)
        sys.exit(1)


if __name__ == "__main__":
    main()
