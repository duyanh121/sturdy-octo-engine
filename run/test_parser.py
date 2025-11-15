import argparse
import time

def weird_parser(s: str) -> str:
    # Crash if the string is too long
    if len(s) > 20:
        raise ValueError("String too long")

    # Trigger TypeError for non-digit content
    if s.isdigit():
        n = int(s)
    else:
        # Intentionally weird: convert letters into a number-ish thing
        n = sum(ord(c) for c in s)

    # Special bad cases
    if n == 42:
        raise RuntimeError("The answer caused a meltdown")

    if n % 5 == 0:
        return "multiple-of-5"

    # Weird slicing
    try:
        part = s[n % len(s)]
    except ZeroDivisionError:
        part = "empty-input"
    except Exception:
        part = "index-error"

    return f"parsed:{part}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("message")
    args = parser.parse_args()

    time.sleep(0.5)

    result = weird_parser(args.message)
    print(result)