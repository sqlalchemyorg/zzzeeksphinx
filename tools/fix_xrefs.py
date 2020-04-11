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
        "".join(line_tokens[0:match_idx])
        + BOLD
        + _token_to_str(line_tokens[match_idx])
        + NORMAL
        + "".join(line_tokens[match_idx + 1 :])
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
        "[e]nter new replacement  [q]uit  [s]? "
    )
    sys.stdout.flush()
    cmd = readchar.readchar()
    print("")
    if cmd == "q":
        sys.exit()
    elif cmd in ("s", "f", "a"):
        return cmd
    elif cmd == "e":
        replacement_text = input("Enter replacement text: ")
        replacements.append(replacement_text)
        return True
    elif isinstance(cmd, int):
        try:
            replacements[cmd]
        except IndexError:
            input("no such replacement %d; press enter to continue" % cmd)
        else:
            return cmd


def tokenize_line(line):
    tokens = []
    start = -1
    mend = 0
    for match in reg.finditer(line):
        mstart, mend = match.span(0)
        if start == -1:
            start = 0
        tokens.append(line[start:mstart])
        tokens.append(match)
        start = mend
    tokens.append(line[mend:])
    return tokens


def process(fname, state):
    with open(fname) as file_:
        lines = list(file_)
        for linenum, line in enumerate(lines):
            line_tokens = tokenize_line(line)
            for idx, token in enumerate(line_tokens):
                if isinstance(token, str):
                    continue

                while True:
                    if token.group(0) not in state:
                        rec = state[token.group(0)] = {
                            "replacements": [],
                            "cmd": None,
                        }
                    else:
                        rec = state[token.group(0)]

                    if rec.get("cmd") == "a":
                        result = "a"
                        break

                    local_replacements = list(rec["replacements"])
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

                if result  == "s":
                    continue  # next line
                elif result == "f":
                    break  # next file
                elif result == "a":
                    rec["cmd"] = "a"  # skip all of these
                elif isinstance(result, int):
                    replacement_text = local_replacements[result]
                    if replacement_text not in rec["replacements"]:
                        rec["replacements"].append(replacement_text)

                    # line = line[0:start] + replacement_text + line[end:]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("filespec", help="file or directory")

    args = parser.parse_args()

    state = {}
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
