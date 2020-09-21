"""Utilities for hanser-py-library"""

import os

from PyPDF2 import PdfFileMerger

HANSER_URL = "https://www.hanser-elibrary.com"


def is_isbn(isbn: str, isbn10_allowed: bool = True) -> bool:
    """True if isbn returns valid ISBN-13 or ISBN-10 checksum"""

    if len(isbn) == 13 and isbn.isnumeric():
        checksum = (
            10 - sum(
                [int(n) * (3 ** (i % 2)) for i, n in enumerate(isbn)]
                ) % 10
            ) % 10

    elif len(isbn) == 10 and isbn[:-1].isnumeric() and isbn10_allowed:
        isbn_parts = list(isbn)
        if not isbn_parts[-1].isnumeric():
            if isbn_parts[-1] not in ("x", "X"):
                return False
            isbn_parts[-1] = "10"

        checksum = sum([int(n) * i for i, n in enumerate(isbn_parts, 1)]) % 11

    else:
        return False

    return bool(checksum == 0)


def log(cat: str, msg: str, div: int = None) -> None:
    """Log categorized message with optional divider"""

    line_length, indent = 79, 10
    log_msg = "{:" + str(indent) + "}{}"

    if "\n" in msg:
        msg = msg.replace("\n", "\n" + " " * indent)

    if div in (0, -1):
        print("-" * line_length)
    print(log_msg.format(cat.upper(), msg))
    if div in (0, 1):
        print("-" * line_length)


def log_download(count: int, chapter: str, total: int) -> None:
    """Logs download of a single chapter"""

    leading = len(str(total)) - len(str(count))
    log("download", f"# {'0' * leading}{count} - {chapter}...")


def write_pdf(pdf: PdfFileMerger, dest: str, name: str) -> bool:
    """Writes content of pdf to a file at the given destination"""

    try:
        pdf.write(os.path.join(dest, name + ".pdf"))
        return True
    except PermissionError:
        raise  # pylint: disable=try-except-raise
    except (FileNotFoundError, OSError):
        return False
