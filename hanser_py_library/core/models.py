"""Data Models for hanser-py-library"""

from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional


@dataclass
class Chapter:
    """Container for title, url and content of a book chapter"""

    title: str
    href: Optional[str] = None
    content: Optional[BytesIO] = None

@dataclass
class Book:
    """Represents metadata for a book"""

    url: str
    authors: List[str]
    chapters: List[Chapter]
    isbn: str
    title: str
    year: int

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
        return "'{}' ({}) \n{} ({} chapters)".format(
            self.title, self.year, authors, len(self.chapters)
        )
