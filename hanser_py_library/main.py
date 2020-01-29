"""
This tool downloads each chapter of a book from hanser-elibrary.com and
merges them into a single PDF File.

:copyright: (c) 2019 by Valentin Weber
:license: GNU General Public License Version 3, see LICENSE
"""

from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
from collections import namedtuple
from io import BytesIO
import os
import sys
from typing import List, Tuple
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger
from requests import get

from . import PROG_NAME

Chapter = namedtuple("Chapter", ["title", "href"])
ApplicationArgs = Tuple[List[str], str, bool]
HanserURLCheck = Tuple[bool, str]


# TODO: Don't exit if error, raise Exception instead
# TODO: If filename raises os error safe file as ISBN.pdf
# TODO: Build Chapter URL with urljoin()
# TODO: URL: https://www.hanser-elibrary.com/doi/book/10.3139/9783446440685

class Application:
    """Application class."""

    HANSER_URL = "https://www.hanser-elibrary.com"

    def __init__(self, output_dir: str, force_dir: bool = False) -> None:

        if not output_dir:
            self.force_dir = True
            self.output_dir = os.getcwd()
        else:
            self.output_dir = output_dir.strip()
            self.force_dir = force_dir

    def hanser_download(self, url: str) -> None:
        """Get title, authors and chapters and check authorization."""

        response = get(url)
        book = BeautifulSoup(response.content, "html.parser")

        if response.status_code == 500:
            sys.exit(book.find("p", class_="error").string)

        title = book.find("div", id="articleToolsHeading").string.strip()
        authors = self.authors_to_string([
            author.string for author in
            book.find_all("span", class_="NLM_string-name")
            ])

        chapter_list = []
        for chapter in book.find_all("table", class_="articleEntry"):

            access = chapter.find("img", class_="accessIcon")["title"]
            if access == "no access":
                sys.exit(f"Unauthorized to download '{title}'")

            chapter_title = chapter.find("span", class_="hlFld-Title").string
            href = chapter.find("a", class_="ref nowrap pdf")["href"]

            if not chapter_title:
                chapter_title = "Chapter " + href.rsplit(".", 1)[1]

            chapter_info = Chapter(chapter_title, href)
            chapter_list.append(chapter_info)

        print(f"Downloading '{title}' by {authors}")

        pdf_list = []
        for chapter in chapter_list:
            print("\t" + "Downloading '" + chapter.title + "'...")
            url = self.HANSER_URL + chapter.href
            download = get(url, params={"download": "true"})
            content = download.headers["Content-Type"].split(";", 1)[0]

            if download.status_code == 200:
                if content == "application/pdf":
                    pdf_list.append(BytesIO(download.content))

                else:
                    sys.exit(f"'{url}' sent {content} not 'application/pdf'")

            else:
                code = download.status_code
                sys.exit(f"'{url}' sent Response Code: {code}")

        print("Download Successful.\n")
        self.merge_and_write_pdf(pdf_list, title)

    def merge_and_write_pdf(self, pdf_list: List[BytesIO], title: str) -> None:
        """Merges all PDFs in pdf_list into one file and saves it"""

        if not pdf_list:
            sys.exit("No PDFs to merge.")

        print("Start Merging '" + title + "'")
        merger = PdfFileMerger()
        for pdf in pdf_list:
            merger.append(pdf)
        print("Merge Complete.\n")

        if len(merger.pages) <= 0:
            sys.exit("No book to save.")

        if not os.path.isdir(self.output_dir) and self.force_dir:
            print("Creating '" + self.output_dir + "'")
            os.makedirs(self.output_dir)

        filename = self.safe_filename(title)
        print("Saving '" + filename + "' to '" + self.output_dir + "'")
        merger.write(os.path.join(self.output_dir, filename))
        print("Done.\n")

    @staticmethod  # TODO: remove & replace with ISBN.pdf
    def safe_filename(name: str) -> str:
        """Remove most non-alnum chars from string and add '.pdf'"""
        return "".join(c for c in name if c.isalnum() or c in "- ._").strip() + ".pdf"

    @staticmethod  # TODO: review this
    def authors_to_string(authors: List[str]) -> str:
        """Return joined string of author names."""

        string = ""
        for i in range(len(authors)):
            names = authors[i].split(",")

            if i == 0:
                sep = ""
            elif i == len(authors) - 1 and i != 0:
                sep = " and "
            else:
                sep = ", "

            string += sep + names[1].strip() + " " + names[0].strip()

        return string


class HanserParser(ArgumentParser):
    """ArgumentParser that validates input."""

    ParserArgFlags = namedtuple("ParserArgFlags", ["short", "long"])

    def __init__(self) -> None:

        example_url = "https://www.hanser-elibrary.com/isbn/9783446450523"
        usage_examples = "EXAMPLES:\n" + "\n".join((
            f"{PROG_NAME} -u {example_url}",
            f"{PROG_NAME} -u {example_url} -o /existing_dir",
            f"{PROG_NAME} -u {example_url} -f -o /dir/to/create"
        ))

        super(HanserParser, self).__init__(
            prog=PROG_NAME,
            description="Download book as pdf from hanser-elibrary.com",
            epilog=usage_examples,
            formatter_class=RawTextHelpFormatter,
        )

        self.out = self.ParserArgFlags("-o", "--out")
        self.force = self.ParserArgFlags("-f", "--force")

        self.add_args()

    def add_args(self) -> None:
        """Add application specific arguments to parser."""

        self.add_argument(
            "url",
            metavar="URL",
            help="URL(s) of book(s) to download",
            type=self.is_application_url,
            nargs="+"
        )

        self.add_argument(
            self.out.short, self.out.long,
            metavar="OUT",
            help="Path to output path. Cannot point to file.",
            type=self.is_valid_dir_path,
            default=""
        )

        self.add_argument(
            self.force.short, self.force.long,
            action="store_true",
            help="Set this to force creation of path to output dir",
            dest="force_dir"
        )

    def validate_args(self):
        """Validate arguments"""

        parsed = self.parse_args()

        if parsed.out and not os.path.isdir(parsed.out):
            if not parsed.force_dir:
                self.error(f"Directory '{parsed.out}' doesn't exist and "
                           f"{'/'.join(self.force)} was not set")

        return parsed.url, parsed.out, parsed.force_dir

    @staticmethod
    def is_application_url(url: str) -> str:
        """Check if URL is valid Application url."""

        if not (url_check := is_hanser_url(url))[0]:
            raise ArgumentTypeError(url_check[1])
        return url_check[1]

    @staticmethod
    def is_valid_dir_path(path: str) -> str:
        """Raise error if path leads to file"""

        if path.startswith("~"):
            path = os.path.normpath(os.path.expanduser(path))

        if os.path.isfile(path):
            raise ArgumentTypeError(f"'{path}' points to a file")
        return path


def is_isbn13(isbn: str) -> bool:
    """True if :isbn: provides valid checksum for ISBN-13"""

    if not isbn.isnumeric() or len(isbn) != 13:
        return False

    checksum = (
        10 - sum(
            [int(isbn[n]) * (3 ** (n % 2)) for n in range(len(isbn))]
            ) % 10
        ) % 10

    return checksum == 0


def is_hanser_url(url: str) -> HanserURLCheck:
    """True if :url: matches is a valid url for hanser-elibrary.com"""

    hanser_url = urlparse(Application.HANSER_URL)
    parsed_url = urlparse(url.strip())

    # Replace missing scheme and fix netloc & path
    if not parsed_url.scheme == hanser_url.scheme:
        if not parsed_url.scheme:

            path_elements = parsed_url.path.split("/", 1)
            if len(path_elements) > 1:
                netloc, fixed_path = path_elements[0], path_elements[1]
            else:
                netloc, fixed_path = path_elements[0], ""

            parsed_url = parsed_url._replace(netloc=netloc, path=fixed_path)
        parsed_url = parsed_url._replace(scheme="https")

    # Check if URL is valid
    err = ""
    url_path = [elem for elem in parsed_url.path.split("/") if elem]
    if parsed_url.netloc not in (hanser_url.netloc, hanser_url.netloc[4:]):
        err = f"Invalid Location: {parsed_url.netloc}"

    elif not url_path[0] == "isbn":
        err = f"URL path must start with 'isbn' not '{url_path[0]}'"

    elif not is_isbn13(url_path[1]):
        err = f"{url_path[1]} returns invalid checksum for ISBN-13"

    if err:
        return False, err

    return True, urlunparse(parsed_url)


def main() -> None:
    """Main entry point."""

    urls, output, force = HanserParser().validate_args()

    app = Application(output, force)
    for book in urls:
        app.hanser_download(book)


if __name__ == '__main__':
    main()
