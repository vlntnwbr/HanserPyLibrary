"""Utilities for hanser-py-library"""

import os
from typing import Tuple

from PyPDF2 import PdfFileMerger, PdfFileReader

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

    line_length, indent = 79, 12
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


class PdfManager:
    """Collection of methods for dealing with pdf-files"""

    def __init__(self, out_dir: str) -> None:
        self.out_dir = out_dir

    def write(self, pdf: PdfFileMerger, name: str) -> str:
        """Writes content of pdf to a file with given name"""

        dest = os.path.join(self.out_dir, name)
        # Append file count to name if other files with same name exist
        file_count = 0
        while True:
            if not os.path.isfile(dest):
                break

            file_count += 1
            names = dest.rsplit(".", 1)
            if file_count == 1:
                names[0] += " (1)"
            else:
                names[0] = names[0].rsplit("(", 1)[0] + f"({file_count})"
            dest = ".".join(names)

        try:
            pdf.write(dest)
            return os.path.split(dest)[1]
        except (FileNotFoundError, OSError):
            # FileNotFound for name containing "/"
            # OSError for other invalid chars in name
            return ""

    @staticmethod
    def merge_pdfs(pdf_files: Tuple[PdfFileReader]) -> PdfFileMerger:
        """Return PdfFileMerger with all pdf-files appended"""
        merger = PdfFileMerger()
        for pdf in pdf_files:
            merger.append(pdf)
        return merger
