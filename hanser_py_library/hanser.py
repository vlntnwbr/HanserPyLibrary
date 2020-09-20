"""Hanser book downloader"""

from io import BytesIO
import os
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger
from requests import get

from .utils import BookMergeError, DownloadError, Chapter


class Application:
    """Application class."""

    HANSER_URL = "https://www.hanser-elibrary.com"

    def __init__(self,
                 url: str,
                 output_dir: str,
                 force_dir: bool = False) -> None:

        self.url = url
        self.isbn = url.rsplit("/", 1)[1]
        self.force_dir = force_dir
        self.authors: str = ""
        self.title: str = ""
        self.chapters: List[Chapter] = []

        if not output_dir:
            self.output_dir = os.getcwd()
        else:
            self.output_dir = output_dir.strip()

    def get_book_info(self) -> None:
        """Get title, authors and chapters and check authorization."""

        response = get(self.url)
        content = BeautifulSoup(response.content, "html.parser")

        if response.status_code in (404, 500):
            raise DownloadError(content.find("p", class_="error").string)

        self.title = content.find(
            "div", id="articleToolsHeading").string.strip()

        no_access = content.find("img", {"class": "accessIcon",
                                         "alt": "no access"})

        if no_access is not None:
            raise DownloadError(f"Unauthorized to download '{self.title}'")

        author_list = [author.string for author in
                       content.find_all("span", class_="NLM_string-name")]

        self.authors = " ".join(
            " ".join(author_list[i].split(", ")[::-1]) + ","
            if i not in (len(author_list) - 1, i != len(author_list) - 2)
            else " ".join(author_list[i].split(", ")[::-1]) + " &"
            if i != len(author_list) - 1
            else " ".join(author_list[i].split(", ")[::-1])
            for i in range(len(author_list)))

        for chapter in content.find_all("table", class_="articleEntry"):

            chapter_title = chapter.find("span", class_="hlFld-Title").string
            href = chapter.find("a", class_="ref nowrap pdf")["href"]
            if not chapter_title:
                chapter_title = "Chapter " + href.rsplit(".", 1)[1]

            self.chapters.append(Chapter(chapter_title, href))

    def download_book(self) -> None:
        """Download PDF content of each chapter"""

        for chapter in self.chapters:
            url = urljoin(self.HANSER_URL, chapter.href)
            download = get(url, params={"download": "true"})
            content = download.headers["Content-Type"].split(";", 1)[0]

            if download.status_code == 200:
                if content == "application/pdf":
                    chapter.content = BytesIO(download.content)

                else:
                    raise DownloadError(
                        f"'{url}' sent {content} not 'application/pdf'")

            else:
                code = download.status_code
                raise DownloadError(f"'{url}' Response Code: {code}")

    def merge_and_write_pdf(self) -> None:
        """Merges all PDFs in pdf_list into one file and saves it"""

        if not self.chapters:
            raise BookMergeError("No PDFs to merge.")

        merged_pdf = PdfFileMerger()
        for pdf in self.chapters:
            merged_pdf.append(pdf.content)

        if len(merged_pdf.pages) <= 0:
            raise BookMergeError("No book to save.")

        if not os.path.isdir(self.output_dir) and self.force_dir:
            os.makedirs(self.output_dir)

        try:
            self._write_pdf(merged_pdf)
        except (FileNotFoundError, OSError):  # save isbn.pdf on error
            self._write_pdf(merged_pdf, self.isbn)

    def _write_pdf(self, pdf: PdfFileMerger,
                   filename: Optional[str] = None) -> None:
        """Write contents of merged PDF to file"""

        if not filename:
            filename = self.title

        pdf.write(os.path.join(self.output_dir, filename + ".pdf"))
