"""
This tool downloads each chapter of a book from hanser-elibrary.com and
merges them into a single PDF File.

:copyright: (c) 2019 by Valentin Weber
:license: GNU General Public License Version 3, see LICENSE
"""

from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
from collections import namedtuple
from io import BytesIO
from os import path, mkdir
import sys
from typing import List, Tuple
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger
from requests import get

Chapter = namedtuple("Chapter", ["title", "href"])
ApplicationArgs = Tuple[List[str], str, bool]
HanserURLCheck = Tuple[bool, str]


class Application(object):
    """Application class."""

    HANSER_URL = "https://www.hanser-elibrary.com"

    def __init__(self, output_dir: str, force_dir: bool = False) -> None:

        if not output_dir:
            self.force_dir = True
            self.output_dir = path.join(
                path.expanduser("~"), "Documents", "HanserPyLibrary"
            )
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

        if not path.isdir(self.output_dir) and self.force_dir:
            print("Creating '" + self.output_dir + "'")
            mkdir(self.output_dir)

        filename = self.safe_filename(title)
        print("Saving '" + filename + "' to '" + self.output_dir + "'")
        merger.write(path.join(self.output_dir, filename))
        print("Done.\n")

    @staticmethod
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


class ApplicationArgParser(ArgumentParser):
    """ArgumentParser that validates input."""

    ParserArgFlags = namedtuple("ParserArgFlags", ["short", "long"])
    USAGES = [
        "py -m hanser_py_library.main -u https://www.hanser-elibrary.com/"
        "isbn/9783446450523",

        "py -m hanser_py_library.main -u https://www.hanser-elibrary.com/"
        "isbn/9783446450523 -o path/to/existing_dir",

        "py -m hanser_py_library.main -u https://www.hanser-elibrary.com/"
        "isbn/9783446450523 -fo path/to/nonexistent_dir"
    ]

    def __init__(self, **parser_args) -> None:

        super(ApplicationArgParser, self).__init__(
            prog=parser_args.get("prog"),
            usage="hanser_py_library.main.py [OPTIONS]",
            description="Download book as pdf from hanser-elibrary.com",
            epilog=f"EXAMPLES:\n" + "\n".join(self.USAGES),
            parents=parser_args.get("parents", []),
            formatter_class=RawTextHelpFormatter,
            prefix_chars=parser_args.get("prefix_chars", "-"),
            fromfile_prefix_chars=parser_args.get("fromfile_prefix_chars"),
            argument_default=parser_args.get("argument_default", None),
            conflict_handler=parser_args.get("conflict_handler", "error"),
            add_help=parser_args.get("add_help", True),
            allow_abbrev=parser_args.get("allow_abbrev", True)
        )

        self.url = self.ParserArgFlags("-u", "--url")
        self.out = self.ParserArgFlags("-o", "--out")
        self.force = self.ParserArgFlags("-fo", "--force")

        self.add_application_args()
        self.application_args = self.parse_args()

    def add_application_args(self) -> None:
        """Add application specific arguments to parser."""

        self.add_argument(
            self.url.short, self.url.long,
            metavar="URL",
            help=f"Book URL starting with '{Application.HANSER_URL}'",
            type=self.application_url,
            default="",
            nargs="*"
        )

        out_help = "Path to custom output directory "
        self.add_argument(
            self.out.short, self.out.long,
            metavar="OUT",
            help=out_help + "that already exists",
            type=self.existing_dir,
            default=""
        )

        self.add_argument(
            self.force.short, self.force.long,
            metavar="FORCE",
            dest="force",
            help=out_help + "that is created if it doesn't exist",
            type=self.valid_dir_path,
            default=False
        )

    def validate_application_args(self) -> ApplicationArgs:
        """Validate arguments from argparse."""
        parsed_out = self.application_args.out
        parsed_force = self.application_args.force

        if parsed_out and parsed_force and (parsed_out != parsed_force):
            msg = f"arguments {'/'.join(self.out)} & {'/'.join(self.force)} " \
                  f"have different values"
            self.error(msg)  # exits with proper argparse.ArgumentError
        elif parsed_force:
            out = parsed_force
            force = True
        else:
            out = parsed_out
            force = False
        # noinspection PyUnboundLocalVariable
        return self.application_args.url, out, force

    @staticmethod
    def application_url(url: str) -> str:
        """Check if URL is valid Application url."""

        if url:
            if not (url_check := is_hanser_url(url))[0]:
                raise ArgumentTypeError(url_check[1])
            return url_check[1]
        return url

    @staticmethod
    def existing_dir(directory: str) -> str:
        """Check if a path exists and is a directory"""

        if directory:
            msg = f"Path '{directory}' "
            if not path.exists(directory):
                msg += "doesn't exist"
            elif path.isfile(directory):
                msg += "is a file not a directory"
            elif not path.isdir(directory):
                msg += "is not a directory"
            if msg[-1] != " ":
                raise ArgumentTypeError(msg)
        return directory

    @staticmethod
    def valid_dir_path(directory: str) -> str:
        """Raise error if path leads to file"""

        if path.isfile(directory):
            msg = f"'{directory}' is a file not a directory"
            raise ArgumentTypeError(msg)
        return directory


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


def get_console_input(get_output: bool = True) -> ApplicationArgs or List[str]:
    """Get at least one URL and an optional output_dir if needed."""

    # Get List of URLs
    multiple_urls = "y"
    urls = []
    while multiple_urls == "y":
        uri_prompt = "Enter URL for 'hanser-elibrary.com' book: "
        while not (url_check := is_hanser_url(input(uri_prompt)))[0]:
            uri_prompt = url_check[1] + "\nPlease enter a valid URL: "

        urls.append(url_check[1])
        multiple_urls = input(f"Added '{url_check[1]}'\n"
                              f"Add another book ? (y) ").lower()

    # Get output directory
    if get_output:
        force = False
        dir_prompt = "[OPTIONAL] Enter path to output dir: "
        while (output_dir := input(dir_prompt)) \
                and not path.isdir(output_dir) and not force:

            msg = f"Directory '{output_dir}' "
            force_out = input(msg + "doesn't exist. Create it? (y) ").lower()
            if force_out == "y":
                if path.isfile(output_dir):
                    print(msg + "is a file not a directory")
                else:
                    force = True
                    break
        return urls, output_dir, force
    return urls


def main() -> None:
    """Main entry point."""

    urls, output, force = ApplicationArgParser().validate_application_args()

    if not urls:
        if not output:
            urls, output, force = get_console_input()
        else:
            urls = get_console_input(get_output=False)

    app = Application(output, force)
    for book in urls:
        app.hanser_download(book)


if __name__ == '__main__':
    main()
