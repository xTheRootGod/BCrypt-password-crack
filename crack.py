#!/usr/bin/env python3

import sys
import os
import time
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
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
CLEAR_LINE = '\033[2K'


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
    words = [w for w in words if w]
    return words


def check_candidate(args):
    password, hash_bytes = args
    try:
        matched = bcrypt.checkpw(password.encode('utf-8', errors='ignore'), hash_bytes)
        return (password, matched)
    except Exception:
        return (password, False)


def format_eta(seconds):
    if seconds is None or seconds == float('inf'):
        return "--:--:--"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def draw_panel(hash_input, total, attempted, current_password, rate, elapsed, eta, workers, status="RUNNING", found_password=None):
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

    pct = (attempted / total * 100) if total else 0
    bar_width = inner - 18
    filled = int(bar_width * attempted / total) if total else 0
    bar = "█" * filled + bcolors.DIM + "░" * (bar_width - filled) + bcolors.ENDC + bcolors.OKCYAN

    rows = []
    rows.append(top)
    rows.append(title_line)
    rows.append(sep)
    rows.append(line(f" Hash      : {hash_input[:inner-13]}"))
    rows.append(line(f" Status    : {status}", bcolors.OKGREEN if status == "RUNNING" else bcolors.FAIL))
    rows.append(line(f" Workers   : {workers}"))
    rows.append(sep)
    rows.append(line(f" Tried     : {attempted:,} / {total:,}  ({pct:5.1f}%)"))
    rows.append(line(f" Speed     : {rate:,.1f} pw/s"))
    rows.append(line(f" Elapsed   : {format_eta(elapsed)}   ETA: {format_eta(eta)}"))
    rows.append(line(f" Current   : {current_password[:inner-13]}"))
    rows.append(sep)
    rows.append(bcolors.OKCYAN + "│" + bar + " " * max(inner - bar_width - len(f" {pct:5.1f}%"), 0) + f" {pct:5.1f}%" + bcolors.OKCYAN + "│" + bcolors.ENDC)
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


def main():
    logo()

    hash_input = input("Hash > ").strip()

    if not is_valid_bcrypt_hash(hash_input):
        print(bcolors.FAIL + "| The provided hash does not look like a valid bcrypt hash "
              "(must start with $2a$, $2b$, $2x$ or $2y$)." + bcolors.ENDC)
        sys.exit(1)

    hash_bytes = hash_input.encode('utf-8')

    passl = input("Enter the path to the wordlist: ").strip()

    if not os.path.exists(passl):
        print(bcolors.FAIL + "| Couldn't find the required list!" + bcolors.ENDC)
        sys.exit(1)

    try:
        plist = load_wordlist(passl)
    except Exception as e:
        print(bcolors.FAIL + f"| Couldn't read the provided wordlist! Error: {e}" + bcolors.ENDC)
        sys.exit(1)

    if not plist:
        print(bcolors.FAIL + "| The wordlist is empty!" + bcolors.ENDC)
        sys.exit(1)

    try:
        max_workers = max(1, (os.cpu_count() or 2) - 1)
    except Exception:
        max_workers = 1

    total = len(plist)
    found_password = None
    attempted = 0
    start_time = time.time()
    panel_lines = 0

    print(HIDE_CURSOR, end='')
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for password in plist:
                fut = executor.submit(check_candidate, (password, hash_bytes))
                futures[fut] = password

            last_draw = 0
            for fut in as_completed(futures):
                attempted += 1
                password, matched = fut.result()

                now = time.time()
                if matched or now - last_draw > 0.1 or attempted == total:
                    last_draw = now
                    elapsed = now - start_time
                    rate = attempted / elapsed if elapsed > 0 else 0
                    remaining = total - attempted
                    eta = remaining / rate if rate > 0 else None

                    panel = draw_panel(
                        hash_input, total, attempted, password, rate,
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
                    for f in futures:
                        f.cancel()
                    break

    except KeyboardInterrupt:
        print(SHOW_CURSOR, end='')
        print(bcolors.WARNING + "\n| Interrupted by user (Ctrl+C). Exiting cleanly." + bcolors.ENDC)
        sys.exit(130)

    print(SHOW_CURSOR, end='')
    print()

    if found_password is not None:
        print(bcolors.OKGREEN + "+---------------------------------------+")
        print(bcolors.OKGREEN + "| Operation completed successfully!")
        print(bcolors.OKGREEN + "| HASH >    " + hash_input)
        print(bcolors.OKGREEN + "| Password >" + " " + found_password)
        print(bcolors.OKGREEN + "+---------------------------------------+" + bcolors.ENDC)
        display_password_details(found_password, hash_input)
        sys.exit(0)
    else:
        print(bcolors.FAIL + "| Password not found. Try with another wordlist." + bcolors.ENDC)
        sys.exit(1)


if __name__ == "__main__":
    main()
