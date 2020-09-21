"""Hanser book downloader"""

from dataclasses import dataclass
from io import BytesIO
import os
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger
import requests

from .exceptions import AccessError, MetaError, MergeError, DownloadError
from .utils import write_pdf


@dataclass
class Chapter:
    """Container for title, url and content of a book chapter"""

    title: str
    href: Optional[str] = None
    content: Optional[BytesIO] = None


@dataclass
class Book:
    """Container for url, authors, chapters, isbn and title of book"""

    url: str
    authors: Optional[str] = None
    chapters: Optional[List[Chapter]] = None
    isbn: Optional[str] = None
    title: Optional[str] = None


class BookParser:  # pylint: disable=too-few-public-methods
    """Search for book and retrieve metadata"""

    def __init__(self, url: str) -> None:
        self.isbn: str = url.rsplit("/", 1)[1]
        self.url = url

    def make_book(self) -> Book:
        """Retrieve authors and title for book"""

        try:
            response = requests.get(self.url)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            if isinstance(exc, requests.exceptions.HTTPError):
                err_msg = f"{self.url} returned {response.status_code}"
            else:
                err_msg = "Unable to establish connection to {self.url}"
            raise AccessError(err_msg) from exc

        book = BeautifulSoup(response.content, "html.parser")
        title_search = book.find("h1", class_="current-issue__title")
        if title_search is None:
            raise MetaError("no title found")
        title = title_search.string.strip()

        if book.find("i", class_="icon-lock") is not None:
            raise AccessError(f"unauthorized to download '{title}'")

        author_search = book.find_all("span", class_="hlFld-ContribAuthor")
        if author_search is None:
            raise MetaError("authors not found")

        author_list = [author.string.strip() for author in author_search]
        if len(author_list) > 1:
            authors = f"{','.join(author_list[:-1])} and {author_list[-1]}"
        else:
            authors = author_list[0]

        chapter_list = []
        section_search = book.find_all("div", class_="issue-item__content")
        for section in section_search:
            chapter_search = section.find("div", class_="issue-item__title")
            href_search = section.find("a", {"title": "PDF"})
            if chapter_search is None or href_search is None:
                raise MetaError("could not retrieve chapter list")
            chapter_list.append(Chapter(
                chapter_search.string,
                href_search["href"].replace("epdf", "pdf")
            ))

        return Book(self.url, authors, chapter_list, self.isbn, title)

    def _get_authors(self) -> str:
        """Parses website for book authors"""

    def _get_chapters(self) -> List[Chapter]:
        """Parses website for chapter titles and references"""

    def _get_title(self) -> str:
        """Parses website for book title"""


class DownloadManager:
    """Download and save a book"""

    def __init__(self, base_url: str, dest: str, force_dest: bool = False):
        self.base_url = base_url
        self.dest = dest
        self.force_dest = force_dest

        if not os.path.isdir(self.dest) and force_dest:
            os.makedirs(self.dest)

    def download_chapter(self, chapter: Chapter) -> Chapter:
        """Download chapter content"""

        url = urljoin(self.base_url, chapter.href)
        try:
            download = requests.get(url, params={"download": "true"})
            download.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise DownloadError from exc

        content = download.headers["Content-Type"].split(";")[0]
        if content != "application/pdf":
            raise DownloadError(f"{download.url} did not send a pdf file")
        chapter.content = BytesIO(download.content)
        return chapter

    def write_book(self, book: Book) -> str:
        """Merge and write book into a single pdf file"""

        if not book.chapters:
            raise MergeError("chapter list is empty")

        merged_book = PdfFileMerger()
        for chapter in book.chapters:
            merged_book.append(chapter.content)

        if len(merged_book.pages) <= 0:
            raise MergeError("merged book contains no pages")

        try:
            filename = book.title
            success = write_pdf(merged_book, self.dest, filename)
            if not success:
                filename = book.isbn
                success = write_pdf(merged_book, self.dest, filename)
                if not success:
                    raise MergeError(f"unable to save book as {filename}.pdf")
        except PermissionError as exc:
            raise MergeError("book already exists") from exc
        return filename + ".pdf"
