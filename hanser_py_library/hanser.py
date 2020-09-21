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
        self.url: str = url
        self.book: BeautifulSoup = None

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
            raise MetaError(err_msg) from exc

        self.book = BeautifulSoup(response.content, "html.parser")
        title = self._get_title()
        authors = self._get_authors()
        chapters = self._get_chapters()

        if self.book.find("i", class_="icon-lock") is not None:
            raise AccessError(f"unauthorized to download '{title}'")

        return Book(self.url, authors, chapters, self.isbn, title)

    def _get_authors(self) -> str:
        """Parses website for book authors"""

        author_list = self.book.find_all("span", class_="hlFld-ContribAuthor")
        if author_list is None:
            raise MetaError("authors not found")

        authors = [author.string.strip() for author in author_list]
        if len(authors) > 1:
            author_string = f"{','.join(authors[:-1])} and {authors[-1]}"
        else:
            author_string = authors[0]
        return author_string

    def _get_chapters(self) -> List[Chapter]:
        """Parses website for chapter titles and references"""

        chapters = []
        chapter_list = self.book.find_all("div", class_="issue-item__content")
        for chapter in chapter_list:
            title_search = chapter.find("div", class_="issue-item__title")
            href_search = chapter.find("a", {"title": "PDF"})
            if title_search is None or href_search is None:
                raise MetaError("could not retrieve chapter list")
            chapters.append(Chapter(
                title_search.string,
                href_search["href"].replace("epdf", "pdf")
            ))
        return chapters

    def _get_title(self) -> str:
        """Parses website for book title"""

        title_search = self.book.find("h1", class_="current-issue__title")
        if title_search is None:
            raise MetaError("no title found")
        return title_search.string.strip()


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
