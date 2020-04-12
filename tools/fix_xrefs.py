#!/usr/bin/env python

import re
import os
import argparse
import sys
import readchar

BOLD = "\033[1m"
NORMAL = "\033[0m"
UNDERLINE = "\033[4m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
DARKCYAN = "\033[36m"
BLUE = "\033[94m"
GREEN = "\033[92m"


def _token_to_str(token):
    if isinstance(token, str):
        return token
    else:
        return token.group(0)


def color(text, color_code):
    return "%s%s%s" % (color_code, text, NORMAL)


def highlighted(line_tokens, match_idx, group):

    match = line_tokens[match_idx]
    display_of_match = (
        BOLD
        + color(
            match.group(0).replace(
                match.group(2), color(match.group(2), CYAN)
            ),
            PURPLE,
        )
        + NORMAL
    )

    return (
        "".join(_token_to_str(tok) for tok in line_tokens[0:match_idx])
        + display_of_match
        + "".join(_token_to_str(tok) for tok in line_tokens[match_idx + 1 :])
    )


def prompt(
    fname, state, lines, linenum, line_tokens, token_idx, rec, replacements, app_state
):
    """Present the prompt screen for a single token in a line in a file and
    receive user input.

    handle_line() calls this function repeated times for a given token
    in a loop until the user command indicates we are done working with
    this particular token.

    """

    if app_state.get("do_prompt", True) and rec.get("do_prompt", True):
        context_lines = 12
        print("\033c")
        print(
            "-----------------------------------------------------------------"
        )
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
        print(
            "-----------------------------------------------------------------"
        )

        print(
            "EXISTING SYMBOL TO REPLACE: %s"
            % color(line_tokens[token_idx].group(2), CYAN)
        )
        print(
            "REPLACEMENTS: %s"
            % " ".join(
                "[%d] %s" % (num, text)
                for num, text in enumerate(replacements, 1)
            )
        )
        print(
            "-----------------------------------------------------------------"
        )

        sys.stdout.write(
            "[s]kip  skip [a]ll of these   skip [f]ile  "
            "[w]rite file and go to next  \n"
            "[A]pply all current non-ambiguous replacements from state\n"
            "[F]inish all files with current "
            "instructions "
            "[e]nter new replacement  \n"
            "[u]se numbered replacement for all "
            "future occurrences [p]db  [q]uit  [s]? "
        )
        sys.stdout.flush()
        cmd = readchar.readchar()
        print("")
        if ord(cmd) in (10, 13):
            cmd = "s"
    else:
        if "apply_all" in rec:
            return rec["apply_all"]
        else:
            return "s"

    if cmd == "q":
        sys.exit()
    elif cmd == "A":
        for rec in state.values():
            if len(rec["replacements"]) == 1 and "apply_all" not in rec:
                rec["apply_all"] = 0
                rec["do_prompt"] = False
        return True
    elif cmd == "F":
        app_state["do_prompt"] = False
        return "s"
    elif cmd in ("s", "f", "a", "w"):
        return cmd
    elif cmd == "p":
        import pdb

        pdb.set_trace()
    elif cmd == "e":
        replacement_text = input(
            "Enter replacement text for the portion in "
            + CYAN
            + "CYAN"
            + NORMAL
            + ": "
        ).strip()
        replacements.append(replacement_text)
        return True
    elif cmd == "u" or re.match(r"\d+", cmd):

        if cmd == "u":
            num = input("Enter number of replacement: ")
            if re.match(r"\d+", num):
                replacement_index = int(num)
            else:
                input("not a number: %s, press enter" % num)
        else:
            replacement_index = int(cmd)

        try:
            replacements[replacement_index - 1]
        except IndexError:
            input(
                "no such replacement %d; press enter to continue"
                % replacement_index
            )
        else:
            if cmd == "u":
                rec["apply_all"] = replacement_index - 1
                rec["do_prompt"] = False
            return replacement_index - 1


reg = re.compile(r"\:(class|attr|func|meth|paramref)\:`(\.\w+).*?`")


def tokenize_line(line):
    """Search a line for py references.

    Return the line as as list of tokens, with non matched portions
    and matched portions together, using Match objects for the matches
    and plain strings for the non matched.

    max_missing_package_tokens indicates which xrefs we will prompt
    for, based on how many package tokens are not present.  zero means
    only xrefs that are straight class, class + method, function etc.
    with no package qualification at all.

    """

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


def process(fname, state, app_state):
    """Parse, process, and write a single file.

    Creates a list of lines and then passes each one off to handle_line().
    handle_line() then has the option to replace that line in the list
    of lines.   The list of lines is then rejoined to write out the new file.

    """

    write = False
    with open(fname) as file_:
        lines = list(file_)

    result = None
    for linenum, line in enumerate(lines):
        result = handle_line(fname, state, lines, linenum, line, app_state)
        if result == "f":  # skipfile
            return
        elif result == "w":  # write and finish
            write = True
            break
        elif result == "c":  # has changes but keep going
            write = True
    if write:
        sys.stdout.write("Writing %s..\n" % fname)
        sys.stdout.flush()
        with open(fname, "w") as file_:
            file_.write("".join(lines))

    return result


def handle_line(fname, state, lines, linenum, line, app_state):
    """Parse, process and replace a single line in a list of lines."""

    if re.match(r'^ *#', line):
        return "n"

    line_tokens = tokenize_line(line)

    if not line_tokens:
        return "n"

    has_replacements = False

    for idx, token in enumerate(line_tokens):
        if isinstance(token, str):
            continue

        if token.group(2) not in state:
            rec = state[token.group(2)] = {
                "replacements": [],
                "cmd": None,
            }
        else:
            rec = state[token.group(2)]

        if rec.get("cmd") == "a":
            # skip all of these, don't do prompt
            result = "s"
        else:
            # do prompt
            local_replacements = list(rec["replacements"])

            while True:
                result = prompt(
                    fname,
                    state,
                    lines,
                    linenum,
                    line_tokens,
                    idx,
                    rec,
                    local_replacements,
                    app_state,
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
        elif result == "F":
            # continue without prompting
            continue

        elif isinstance(result, int):
            replacement_text = local_replacements[result]
            if replacement_text not in rec["replacements"]:
                rec["replacements"].append(replacement_text)
                write_replacement_rec(token.group(2), replacement_text)
            has_replacements = True
            line_tokens[idx] = token.group(0).replace(
                token.group(2), replacement_text
            )

    if has_replacements:
        newline = reformat_line(line_tokens)
        lines[linenum] = newline
        return "c"


def reformat_line(line_tokens, length=79):
    """Given line tokens where one or more of the tokens has been replaced,
    write out a new line, while ensuring that the max length is maintained.

    When the resulting line would be longer than the length, the line is
    split at that point.    Heuristics are used to determine what the
    left-leading indentation should be, as well as if individual lines
    have quotes on both sides.

    """
    line_tokens = [_token_to_str(token) for token in line_tokens]
    printed_line = "".join(line_tokens)
    if len(printed_line) <= length:
        return printed_line

    whitespace = re.match(r"^( +)", printed_line)
    if whitespace:
        whitespace = whitespace.group(1)
    else:
        whitespace = ""

    quote_char = ""
    stripped = printed_line.strip()
    if stripped[0] in "'\"":
        quote_char = stripped[0]
        if stripped[-1] != quote_char:
            quote_char = ""

    len_ = 0
    for idx, token in enumerate(line_tokens):

        len_ += len(token)
        if len_ >= length:
            len_ = 0

            if idx > 0:
                line_tokens[idx - 1] = (
                    line_tokens[idx - 1].rstrip()
                    + (" " if quote_char else "")
                    + quote_char
                )
            token = "\n" + whitespace + quote_char + token.lstrip()
        line_tokens[idx] = token

    return "".join(line_tokens)


state_file_name = "fix_xref_state.txt"


def restore_state_file():
    """Read the state file if any and restore existing replacement tokens
    that were established from a previous run.

    """
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
    """Write a single replacement token to the state file."""
    with open(state_file_name, "a") as file_:
        file_.write("%s %s\n" % (old, new))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("filespec", help="file or directory", nargs="+")

    args = parser.parse_args()

    state = restore_state_file()
    app_state = {}

    for filespec in args.filespec:
        file_ = os.path.abspath(filespec)
        if os.path.isdir(file_):
            for root, dirs, files in os.walk(file_):
                for fname in files:
                    if not fname.endswith(".py") and not fname.endswith(
                        ".rst"
                    ):
                        continue
                    process(os.path.join(root, fname), state, app_state)
        else:
            process(file_, state, app_state)


if __name__ == "__main__":
    main()
