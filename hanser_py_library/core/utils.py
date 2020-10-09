##
#   Copyright (c) 2020 Valentin Weber
#
#   This file is part of hanser-py-library.
#
#   hanser-py-library is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   hanser-py-library is distributed in the hope that it will be
#   useful, but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with hanser-py-library. If not, see
#   <https://www.gnu.org/licenses/#GPL>.
##

"""Utilities for hanser-py-library"""

import os
import textwrap
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


def is_write_protected(path: str) -> bool:
    """Return true if gived directory is write protected"""

    dest = PdfManager.append_file_count(os.path.join(path, "access.txt"))
    try:
        with open(dest, "w"):
            pass
    except PermissionError:
        return True
    os.remove(dest)
    return False


class Logger:
    """Provide simple formatted console output methods"""

    def __init__(self, line_length: int, indent: int) -> None:
        self.line_length = line_length
        self.indent = indent

    def download(self, count: int, chapter: str, total: int) -> None:
        """Logs download of a single chapter"""

        leading = len(str(total)) - len(str(count))
        prefix = f"# {'0' * leading}{count} - "

        if chapter is None:
            chapter = f"Chapter {count}"

        msg = textwrap.fill(
            prefix + chapter,
            width=self.line_length - self.indent,
            subsequent_indent=" " * len(prefix)
        )
        self("download", msg)

    def __call__(self, cat: str, msg: str, div: int = None) -> None:
        """Log categorized message with optional divider"""

        log_msg = "{:" + str(self.indent) + "}{}"
        if "\n" in msg:
            msg = msg.replace("\n", "\n" + " " * self.indent)

        if div in (0, -1):
            print("-" * self.line_length)
        print(log_msg.format(cat.upper(), msg))
        if div in (0, 1):
            print("-" * self.line_length)


class PdfManager:
    """Collection of methods for dealing with pdf-files"""

    def __init__(self, out_dir: str) -> None:
        self.out_dir = out_dir

    def write(self, pdf: PdfFileMerger, name: str) -> str:
        """Writes content of pdf to a file with given name"""

        dest = self.append_file_count(os.path.join(self.out_dir, name))
        try:
            pdf.write(dest)
            return os.path.split(dest)[1]
        except (FileNotFoundError, OSError):
            # FileNotFound for name containing "/"
            # OSError for other invalid chars in name
            return ""

    @staticmethod
    def append_file_count(dest: str) -> str:
        """Append file count to dest if files with same name exist"""

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
        return dest

    @staticmethod
    def merge_pdfs(pdf_files: Tuple[PdfFileReader]) -> PdfFileMerger:
        """Return PdfFileMerger with all pdf-files appended"""
        merger = PdfFileMerger()
        for pdf in pdf_files:
            merger.append(pdf)
        return merger
