"""
This tool downloads each chapter of a book from hanser-elibrary.com and
merges them into a single PDF File.

:copyright: (c) 2019 by Valentin Weber
:license: GNU General Public License Version 3, see LICENSE
"""

from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
from dataclasses import dataclass
from io import BytesIO
import os
import sys
import textwrap
from typing import List, Optional, Tuple
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger
from requests import get

from . import PROG_NAME, PROG_DESC


class DownloadError(Exception):
    """Exception that occurs while the book is downloaded"""


class BookMergeError(Exception):
    """Error that occurs while merging the book"""


@dataclass
class Chapter:
    """Chapter data."""

    title: str
    href: Optional[str] = None
    content: Optional[BytesIO] = None


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
            log("download", chapter.title, -1, "-")
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
        log("info", "Merge Complete.", -1, "-")

        if len(merged_pdf.pages) <= 0:
            raise BookMergeError("No book to save.")

        if not os.path.isdir(self.output_dir) and self.force_dir:
            log("info", f"Creating '{self.output_dir}'", -1, "-")
            os.makedirs(self.output_dir)

        try:
            log("info",
                f"Saving '{self.title}.pdf' to '{self.output_dir}'",
                -1, "-")
            self._write_pdf(merged_pdf)
        except (FileNotFoundError, OSError):
            log("warning", "Filename contains invalid characters.", 0, "*")
            log("info", f"Saving as '{self.isbn}.pdf' instead")
            self._write_pdf(merged_pdf, self.isbn)

    def _write_pdf(self, pdf: PdfFileMerger,
                   filename: Optional[str] = None) -> None:
        """Write contents of merged PDF to file"""

        if not filename:
            filename = self.title

        pdf.write(os.path.join(self.output_dir, filename + ".pdf"))


class HanserParser(ArgumentParser):
    """ArgumentParser that validates input."""

    def __init__(self) -> None:

        example_url = "https://www.hanser-elibrary.com/isbn/9783446450523"
        usage_examples = "EXAMPLES:\n" + "\n".join((
            f"{PROG_NAME} {example_url}",
            f"{PROG_NAME} -o /existing_dir {example_url}",
            f"{PROG_NAME} -o /dir/to/create -f {example_url} "
        ))

        super(HanserParser, self).__init__(
            prog=PROG_NAME,
            description=PROG_DESC,
            epilog=usage_examples,
            formatter_class=RawTextHelpFormatter,
        )

        self.add_args()

    def add_args(self) -> None:
        """Add application specific arguments to parser."""

        self.add_argument(
            "url",
            metavar="URL",
            help="URL(s) of book(s) to download",
            type=self.is_application_url,
            nargs="*"
        )

        self.add_argument(
            "-o", "--out",
            metavar="OUT",
            help="Path to output path. Cannot point to file.",
            type=self.is_valid_dir_path,
            default=""
        )

        self.add_argument(
            "-f", "--force",
            action="store_true",
            help="Set this to force creation of path to output dir",
            dest="force_dir"
        )

        self.add_argument(
            "--isbn",
            help="ISBN(s) of book(s) to download. Can be either ISBN-10 or 13",
            type=self.isbn_to_hanser_url,
            nargs="*",
            default=[]
        )

    def validate_args(self) -> Tuple[List[str], str, bool]:
        """Validate arguments"""

        parsed = self.parse_args()

        if not parsed.url and not parsed.isbn:
            self.error(
                "at least one of the following arguments is required: "
                "URL, --isbn")

        if parsed.out and not os.path.isdir(parsed.out):
            if not parsed.force_dir:
                self.error(f"Directory '{parsed.out}' doesn't exist and "
                           f"-f/--force was not set")

        return parsed.isbn + parsed.url, parsed.out, parsed.force_dir

    @staticmethod
    def isbn_to_hanser_url(isbn: str) -> str:
        """Turn a valid isbn string into an URL for hanser-elibrary"""

        if isbn:
            if not is_isbn(isbn):
                raise ArgumentTypeError(
                    f"'{isbn}' returns invalid ISBN checksum")
            return urljoin(Application.HANSER_URL, "/".join(["isbn", isbn]))
        return isbn

    @staticmethod
    def is_application_url(url: str) -> str:
        """Check if URL is valid Application url."""

        hanser_url = urlparse(Application.HANSER_URL)
        parsed_url = urlparse(url.strip())

        # Replace missing/invalid scheme and build correct netloc & path
        if not parsed_url.scheme == hanser_url.scheme:
            if not parsed_url.scheme:

                path_elements = parsed_url.path.split("/", 1)
                if len(path_elements) > 1:
                    netloc, path = path_elements[0], path_elements[1]
                else:
                    netloc, path = path_elements[0], ""

                parsed_url = parsed_url._replace(netloc=netloc, path=path)
            parsed_url = parsed_url._replace(scheme="https")

        # Check if URL is valid
        if parsed_url.netloc not in (hanser_url.netloc, hanser_url.netloc[4:]):
            raise ArgumentTypeError(f"Invalid Location: {parsed_url.netloc}")

        path_list = [elem for elem in parsed_url.path.split("/") if elem]
        path_str = "/".join(path_list)
        path_err = "path must start with '{}' not '{}'"

        if (elements := len(path_list)) != 2 and elements != 4:  # noqa pylint: disable=E0601
            err = f"invalid amount of path elements in '{path_str}'"
            raise ArgumentTypeError(err)

        if elements == 4 and not path_str.startswith("doi/book/"):
            err = path_err.format("doi/book/<DOI>", path_str)
            raise ArgumentTypeError(err)

        if elements == 2 and not path_list[0] == "isbn":
            err = path_err.format("isbn", path_list[0])
            raise ArgumentTypeError(err)

        allow_isbn10 = bool(elements == 2)
        if not is_isbn(path_list[-1], allow_isbn10):
            err = f"path end {path_list[-1]} returns invalid ISBN checksum"
            raise ArgumentTypeError(err)

        return parsed_url._replace(path=path_str).geturl()

    @staticmethod
    def is_valid_dir_path(path: str) -> str:
        """Raise error if path leads to file"""

        if path.startswith("~"):
            path = os.path.normpath(os.path.expanduser(path))

        if path.startswith("."):
            path = os.path.abspath(path)

        if os.path.isfile(path):
            raise ArgumentTypeError(f"'{path}' points to a file")
        return path


def is_isbn(isbn: str, isbn10_allowed: bool = True) -> bool:
    """True if given isbn returns valid ISBN-13 or ISBN-10 checksum"""

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


def log(category: str, message: str,
        div: Optional[int] = None, div_char: str = "=", end: str = "") -> None:
    """Print a message with an optional divider"""

    message = "{:10}{}".format(category.upper(), message)
    div_str = div_char * 79

    if div in (-1, 0):
        print(div_str)

    message = textwrap.fill(message, 79, subsequent_indent=" " * 10)
    print(message)

    if div in (0, 1):
        print(div_str, end=end + "\n")


def main() -> None:
    """Main entry point."""

    urls, output, force = HanserParser().validate_args()
    for url in urls:
        book = Application(url, output, force)
        err_msg = "Skipped ISBN " + book.isbn + " due to: {} error: {}"

        try:
            log("info", f"Getting chapters for ISBN: {book.isbn}", 0)
            book.get_book_info()
            chapter_msg = "Start {} '" + book.title + "' by " + book.authors
            log("info", chapter_msg.format("downloading"))
            book.download_book()
            log("info", "Download successful!", 0)
            log("info", chapter_msg.format("merging"))
            book.merge_and_write_pdf()
            log("done", "", 0, end="\n")

        except DownloadError as exc:
            log("error", err_msg.format("download", exc.args[0]), 0, "+", "\n")
        except BookMergeError as exc:
            log("error", err_msg.format("merge", {exc.args[0]}), 0, "+", "\n")
        except KeyboardInterrupt:
            log("exit", "Aborting and exiting Program...", 0)
            sys.exit()

    log("exiting", "")


if __name__ == '__main__':
    main()
