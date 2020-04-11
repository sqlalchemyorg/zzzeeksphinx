#!/usr/bin/env python

import re
import os
import argparse
import sys
import readchar

BOLD = "\033[1m"
NORMAL = "\033[0m"
UNDERLINE = "\033[4m"


reg = re.compile(r"\:(class|attr|func|meth|paramref)\:`(.+?)`")


def _token_to_str(token):
    if isinstance(token, str):
        return token
    else:
        return token.group(0)


def highlighted(line_tokens, match_idx, group):
    return (
        "".join(_token_to_str(tok) for tok in line_tokens[0:match_idx])
        + BOLD
        + _token_to_str(line_tokens[match_idx])
        + NORMAL
        + "".join(_token_to_str(tok) for tok in line_tokens[match_idx + 1 :])
    )


def prompt(fname, lines, linenum, line_tokens, token_idx, rec, replacements):
    context_lines = 12
    print("\033c")
    print("-----------------------------------------------------------------")
    print(UNDERLINE + fname + NORMAL)
    print("")
    for index in range(
        linenum - context_lines // 2, linenum + context_lines // 2
    ):
        if index >= 0 and index <= len(lines):
            if index == linenum:
                content = highlighted(line_tokens, token_idx, 0).rstrip()
            else:
                content = lines[index].rstrip()
            print("%4.d: %s" % (index + 1, content))
    print("-----------------------------------------------------------------")

    print("EXISTING TEXT: %s" % line_tokens[token_idx].group(0))
    print(
        "REPLACEMENTS: %s"
        % " ".join(
            "[%d] %s" % (num, text) for num, text in enumerate(replacements, 1)
        )
    )
    print("-----------------------------------------------------------------")

    sys.stdout.write(
        "[s]kip  skip [a]ll of these   skip [f]ile  "
        "[w]rite file and go to next  "
        "[e]nter new replacement  [p]db  [q]uit  [s]? "
    )
    sys.stdout.flush()
    cmd = readchar.readchar()
    print("")
    if ord(cmd) in (10, 13):
        cmd = "s"

    if cmd == "q":
        sys.exit()
    elif cmd in ("s", "f", "a", "w"):
        return cmd
    elif cmd == "p":
        import pdb

        pdb.set_trace()
    elif cmd == "e":
        replacement_text = input("Enter replacement text: ").strip()
        replacements.append(replacement_text)
        return True
    elif re.match(r"\d+", cmd):
        replacement_index = int(cmd)
        try:
            replacements[replacement_index - 1]
        except IndexError:
            input(
                "no such replacement %d; press enter to continue"
                % replacement_index
            )
        else:
            return replacement_index - 1


def tokenize_line(line):
    tokens = []
    start = -1
    mend = 0
    has_tokens = False
    for match in reg.finditer(line):
        has_tokens = True
        mstart, mend = match.span(0)
        if start == -1:
            start = 0
        tokens.append(line[start:mstart])
        tokens.append(match)
        start = mend
    tokens.append(line[mend:])

    if has_tokens:
        return tokens
    else:
        return None


def process(fname, state):
    write = False
    with open(fname) as file_:
        lines = list(file_)

    for linenum, line in enumerate(lines):
        result = handle_line(fname, state, lines, linenum, line)
        if result == "f":  # skipfile
            return
        elif result == "w":  # write and finish
            write = True
            break
        elif result == "c":  # has changes but keep going
            write = True
    if write:
        write_lines(fname, lines)

def write_lines(fname, lines):
    with open(fname, "w") as file_:
        file_.write("".join(lines))

def handle_line(fname, state, lines, linenum, line):
    line_tokens = tokenize_line(line)

    if not line_tokens:
        return "n"

    has_replacements = False

    for idx, token in enumerate(line_tokens):
        if isinstance(token, str):
            continue

        if token.group(0) not in state:
            rec = state[token.group(0)] = {
                "replacements": [],
                "cmd": None,
            }
        else:
            rec = state[token.group(0)]

        if rec.get("cmd") == "a":
            # skip all of these, don't do prompt
            result = "s"
        else:
            # do prompt
            local_replacements = list(rec["replacements"])

            while True:
                result = prompt(
                    fname,
                    lines,
                    linenum,
                    line_tokens,
                    idx,
                    rec,
                    local_replacements,
                )
                if result is True:
                    continue
                else:
                    break

        if result in ("f", "w"):
            return result  # skipfile
        elif result == "s":
            continue  # skip this token
        elif result == "a":
            rec["cmd"] = "a"  # skip all of these
            continue
        elif isinstance(result, int):
            replacement_text = local_replacements[result]
            if replacement_text not in rec["replacements"]:
                rec["replacements"].append(replacement_text)
                write_replacement_rec(token.group(0), replacement_text)
            has_replacements = True
            line_tokens[idx] = replacement_text

    if has_replacements:
        newline = reformat_line(line_tokens)
        lines[linenum] = newline
        return "c"

def reformat_line(line_tokens, length=79):
    line_tokens = [_token_to_str(token) for token in line_tokens]
    printed_line = "".join(line_tokens)
    if len(printed_line) <= length:
        return printed_line

    whitespace = re.match(r'^( +)', printed_line)
    if whitespace:
        whitespace = whitespace.group(1)
    else:
        whitespace = ""

    quote_char = ""
    stripped = printed_line.strip()
    if stripped[0] in '\'"':
        quote_char = stripped[0]
        if stripped[-1] != quote_char:
            quote_char = ""

    len_ = 0
    for idx, token in enumerate(line_tokens):

        len_ += len(token)
        if len_ >= length:
            len_ = 0

            if idx > 0:
                line_tokens[idx - 1] = line_tokens[idx - 1].rstrip()
            token = "\n" + whitespace + quote_char + token.lstrip()
        line_tokens[idx] = token

    return "".join(line_tokens)


state_file_name = "fix_xref_state.txt"

def restore_state_file():
    state = {}
    if not os.path.exists(state_file_name):
        return state

    with open(state_file_name, "r") as file_:
        for line in file_:
            old, new = line.strip().split(" ", 1)
            if old not in state:
                state[old] = rec = {
                    "replacements": [],
                    "cmd": None,
                }
            else:
                rec = state[old]

            if new not in rec["replacements"]:
                rec["replacements"].append(new)

    return state

def write_replacement_rec(old, new):
    with open(state_file_name, "a") as file_:
        file_.write("%s %s\n" % (old, new))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("filespec", help="file or directory")

    args = parser.parse_args()

    state = restore_state_file()

    file_ = os.path.abspath(args.filespec)
    if os.path.isdir(file_):
        for root, dirs, files in os.walk(file_):
            for fname in files:
                if not fname.endswith(".py") and not fname.endswith(".rst"):
                    continue
                process(fname, state)
    else:
        process(file_, state)


if __name__ == "__main__":
    main()
