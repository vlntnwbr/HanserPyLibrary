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

"""Data Models for hanser-py-library"""

from dataclasses import dataclass
from typing import List, Optional

from PyPDF2 import PdfFileMerger, PdfFileReader


@dataclass
class Chapter:
    """Container for title, url and content of a book chapter"""

    title: str
    href: str
    content: Optional[PdfFileReader] = None


@dataclass
class Book:
    """Represents metadata for a book"""

    authors: List[str]
    chapters: List[Chapter]
    complete_available: str
    isbn: str
    title: str
    year: int
    contents: Optional[PdfFileMerger] = None

    def __repr__(self):
        return f"{self.__class__}({self.__dict__})"

    def __str__(self):

        if None in (self.authors, self.chapters, self.isbn, self.title):
            return self.__repr__()

        if len(self.authors) == 1:
            authors = self.authors[0]
        elif len(self.authors) == 2:
            authors = f"{self.authors[0]} and {self.authors[1]}"
        else:
            authors = f"{self.authors[:2]} et al."

        string = "{} ({}) \n{} ({} chapters)".format(
            self.title, self.year, authors, len(self.chapters)
        )

        if self.complete_available:
            string += "\nComplete Book PDF is available"

        return string
