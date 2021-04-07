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

"""Hanser book downloader"""

from io import BytesIO
from urllib.parse import urljoin
import re
from typing import List

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger, PdfFileReader
import requests

from .core.exceptions import AccessError, MetaError, MergeError, DownloadError
from .core.models import Chapter, Book
from .core.utils import PdfManager


class BookParser():
    """Search for book and retrieve metadata"""

    def __init__(self, url: str) -> None:
        self.isbn: str = url.rsplit("/", 1)[1]
        self.url: str = url

        try:
            response = requests.get(self.url)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            if isinstance(exc, requests.exceptions.HTTPError):
                if response.status_code == 404:
                    err_msg = f"Unable to locate book with ISBN {self.isbn}"
                else:
                    err_msg = f"{self.url} returned {response.status_code}"
            else:
                err_msg = "Unable to establish connection"
            raise MetaError(err_msg) from exc

        self.book = BeautifulSoup(response.content, "html.parser")

    def make_book(self) -> Book:
        """Collect all book metadata to prepare download"""

        title = self.get_title()
        authors = self.get_authors()
        chapters = self.get_chapters()
        year = self.get_year()
        complete = self.get_complete_url()
        unauthorized_check = self.book.find(
            "i", {"class": "icon-lock", "aria-hidden": "true"}
        )

        if unauthorized_check is not None:
            raise AccessError(f"unauthorized to download '{title}'")

        return Book(authors, chapters, complete, self.isbn, title, year)

    def get_authors(self) -> List[str]:
        """Parses website for book authors"""

        author_list = self.book.find_all("span", class_="hlFld-ContribAuthor")
        if not author_list:
            raise MetaError("authors not found")

        return [author.string.strip() for author in author_list]

    def get_chapters(self) -> List[Chapter]:
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

    def get_title(self) -> str:
        """Parses website for book title"""

        title_search = self.book.find("h1", class_="current-issue__title")
        if title_search is None:
            raise MetaError("no title found")
        return title_search.string.strip()

    def get_year(self) -> int:
        """Parses website for the year the book was published"""

        text_filter = re.compile(r"^© \d\d\d\d")
        year = self.book.find("span", string=text_filter)
        if year is None:
            raise MetaError("year of publication not found")
        return int(year.string.strip()[2:6])

    def get_complete_url(self) -> int:
        """Gets download URL for complete book PDF"""

        check = self.book.find("a", {"title": "Complete Book PDF"})
        return "" if check is None else check["href"].replace("epdf", "pdf")


class DownloadManager:
    """Download and save a book"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def download_chapter(self, chapter: Chapter) -> Chapter:
        """Download chapter content"""

        url = urljoin(self.base_url, chapter.href)
        chapter.content = PdfFileReader(self._get_pdf(url))
        return chapter

    def download_book(self, url: str) -> PdfFileMerger:
        """Download Complete book pdf"""
        book = PdfFileMerger()
        book.append(self._get_pdf(urljoin(self.base_url, url)))
        return book

    @staticmethod
    def write_book(book: Book, dest: str) -> str:
        """Merge and write book into a single pdf file"""

        pdf_helper = PdfManager(dest)
        if book.contents is None:
            book.contents = pdf_helper.merge_pdfs((
                chapter.content for chapter in book.chapters
            ))

        if len(book.contents.pages) <= 0:
            raise MergeError("merged book contains no pages")

        filename = book.title + "-" + str(book.year) + ".pdf"
        saved = pdf_helper.write(book.contents, filename)
        if not saved:
            filename = "ISBN_" + book.isbn + "-" + str(book.year) + ".pdf"
            saved = pdf_helper.write(book.contents, filename)
            if not saved:
                raise MergeError(f"unable to save book as {filename}")
        return saved

    @staticmethod
    def _get_pdf(url: str) -> BytesIO:
        """Send get request to url and check for Content-Type pdf"""

        try:
            download = requests.get(url, params={"download": "true"})
            download.raise_for_status()
        except requests.exceptions.RequestException as exc:
            if isinstance(exc, requests.exceptions.HTTPError):
                err_msg = f"{url} returned {download.status_code}"
            elif isinstance(exc, requests.exceptions.Timeout):
                err_msg = f"connection to {url} timed out"
            elif isinstance(exc, requests.exceptions.ConnectionError):
                err_msg = f"unable to reach {url}"
            else:
                err_msg = f"connection to {url} failed"
            raise DownloadError(err_msg) from exc

        content = download.headers["Content-Type"].split(";")[0]
        if content != "application/pdf":
            raise DownloadError(f"{download.url} did not send a pdf file")
        return BytesIO(download.content)
