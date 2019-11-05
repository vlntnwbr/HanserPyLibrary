"""
This tool downloads each chapter of a book from hanser-elibrary.com and
merges them into a single PDF File.

:copyright: (c) 2019 by Valentin Weber
:license: GNU General Public License Version 3, see LICENSE
"""

from argparse import ArgumentParser, ArgumentTypeError, HelpFormatter
from collections import namedtuple
from io import BytesIO
from os import path, mkdir
from typing import List, Tuple

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger
from requests import get

Chapter = namedtuple("Chapter", ["title", "href"])
ApplicationArgs = Tuple[List[str], str]


class Application(object):
    """Application class."""

    BASE_URL = "https://www.hanser-elibrary.com"

    def __init__(self, url: str, output_dir: str, force_dir: bool = False):
        self.url = url.strip()
        self.title = ""  # Book title
        self.authors = []  # List of authors
        self.chapter_list = []  # Chapter: URL
        self.chapters = []  # Contains downloaded PDFs
        self.book = PdfFileMerger()  # Merged Book

        if not output_dir:
            self.force_dir = True
            self.output_dir = path.join(
                path.expanduser("~"), "Documents", "HanserPyLibrary"
            )
        else:
            self.output_dir = output_dir.strip()
            self.force_dir = force_dir

    def run(self):
        """Starts and exists the application."""

        self.get_book_info()
        self.download_book()
        self.merge_pdf()
        self.write_pdf(self.title)

    def get_book_info(self):
        """Get title, authors and chapters and check authorization."""

        response = get(self.url)
        book = BeautifulSoup(response.content, "html.parser")

        if response.status_code == 500:
            error = book.find("p", class_="error").string
            exit_script(error, 500)

        self.title = book.find("div", id="articleToolsHeading").string.strip()
        self.authors = [
            author.string for author in
            book.find_all("span", class_="NLM_string-name")
        ]

        for chapter in book.find_all("table", class_="articleEntry"):

            access = chapter.find("img", class_="accessIcon")["title"]
            if access == "no access":
                error = "Unauthorized to download '" + self.title + "'"
                exit_script(error, 401)

            title = chapter.find("span", class_="hlFld-Title").string
            href = chapter.find("a", class_="ref nowrap pdf")["href"]

            if not title:
                title = "Chapter " + href.rsplit(".", 1)[1]

            chapter_info = Chapter(title, href)
            self.chapter_list.append(chapter_info)

    def download_book(self):
        """Download every chapter of book."""

        if not self.chapter_list:
            exit_script("No Chapters to download.", 1)

        print(
            "Downloading '" + self.title + "' by " + self.authors_to_string()
            )
        for chapter in self.chapter_list:
            print("\t" + "Downloading '" + chapter.title + "'...")
            url = self.BASE_URL + chapter.href
            download = get(url, params={"download": "true"})
            content = download.headers["Content-Type"].split(";", 1)[0]

            if download.status_code == 200:
                if content == "application/pdf":
                    pdf = BytesIO(download.content)
                    self.chapters.append(pdf)
                else:
                    exit_script(
                        url + "sent '" + content + "' not 'application/pdf'", 2
                    )
            else:
                code = download.status_code
                exit_script(
                    url + "Response Code: " + str(code), code
                )

        print("Download Successful.\n")

    def merge_pdf(self):
        """Merges all chapters into one PDF file."""

        if not self.chapters:
            exit_script("No chapters to merge.", 3)

        print("Start Merging '" + self.title + "'")
        for pdf in self.chapters:
            self.book.append(pdf)
        print("Merge Complete.\n")

    def write_pdf(self, filename: str):
        """Save merged PDF."""

        if len(self.book.pages) > 0:
            filename = safe_filename(filename)

            if not path.isdir(self.output_dir) and self.force_dir:
                print("Creating '" + self.output_dir + "'")
                mkdir(self.output_dir)

            print("Saving '" + filename + "' to '" + self.output_dir + "'")
            self.book.write(path.join(self.output_dir, filename))
            print("Done.\n")
        else:
            exit_script("No book to save.", 4)

    def authors_to_string(self) -> str:
        """Return joined string of author names."""

        authors = ""
        for i in range(len(self.authors)):
            names = self.authors[i].split(",")

            if i == 0:
                sep = ""
            elif i == len(self.authors) - 1 and i != 0:
                sep = " and "
            else:
                sep = ", "

            authors += sep + names[1].strip() + " " + names[0].strip()

        return authors

    def print_attributes(self):
        """Print all attributes."""
        print(self.title)
        print(self.authors)
        print(self.chapter_list)
        print(self.chapters)
        print(len(self.book.pages))
        print(self.output_dir)


def safe_filename(name: str):
    """Remove most non-alum chars from string and add '.pdf'"""
    return "".join(c for c in name if c.isalnum() or c in "- ._").strip() + ".pdf"


def exit_script(message: str, code: int = 0):
    """Display error and wait for input to exit script"""

    if code:
        message = "\n" + "ERROR: " + message

    print(message)
    input("Press ENTER to exit ")
    exit(code)


class ApplicationArgParser(ArgumentParser):
    """ArgumentParser that validates input"""
    
    def __init__(self, **parser_args):
        super(ApplicationArgParser, self).__init__(
            prog=parser_args.get("prog"),
            usage=parser_args.get("usage"),
            description=parser_args.get("description"),
            epilog=parser_args.get("epilog"),
            parents=parser_args.get("parents", []),
            formatter_class=parser_args.get("formatter_class", HelpFormatter),
            prefix_chars=parser_args.get("prefix_chars", "-"),
            fromfile_prefix_chars=parser_args.get("fromfile_prefix_chars"),
            argument_default=parser_args.get("argument_default", None),
            conflict_handler=parser_args.get("confilct_handler", "error"),
            add_help=parser_args.get("add_help", True),
            allow_abbrev=parser_args.get("allow_abbrev", True)
        )

        self.add_application_args()
        self.application_args = self.parse_args()

    def add_application_args(self):
        """Add application specific arguments to parser"""
        self.add_argument(
            "-u", "--url",
            metavar="url",
            help=f"Book URL starting with '{Application.BASE_URL}'",
            type=self.application_url,
            default="",
            nargs="*"
        )

        self.add_argument(
            "-o", "--out",
            metavar="out",
            help="Path to custom directory that already exists",
            type=self.existing_dir,
            default=""
        )

    def validate_application_args(self) -> ApplicationArgs:
        """Validate arguments from argparse"""
        return self.application_args.url, self.application_args.out

    @staticmethod
    def application_url(url: str):
        """Check if URL is valid Application url"""
        if url and not url.startswith(Application.BASE_URL):
            msg = f"'{url}' doesn't start with '{Application.BASE_URL}'"
            raise ArgumentTypeError(msg)
        return url

    @staticmethod
    def existing_dir(directory: str):
        """Check if directory exists"""
        if directory and not path.isdir(directory):
            msg = f"'{directory}' isn't a directory"
            raise ArgumentTypeError(msg)
        return directory


def get_console_input(get_output: bool = True) -> ApplicationArgs or List[str]:
    """Get at least one URL and an optional output_dir if needed."""

    # Force Creation option for nonexistent output_dir (check if path is file)
    # Get List of URLs
    uri_prompt = "Enter URI for 'hanser-elibrary.com' book: "
    multiple_urls = "y"
    urls = []
    while multiple_urls == "y":
        while not (url := input(uri_prompt)).startswith(Application.BASE_URL):
            original_prompt = uri_prompt
            uri_prompt = "Please enter a valid URI: "

        urls.append(url)
        if (multiple_urls := input("Add another book ? (y) ").lower()) == "y":
            try:
                # noinspection PyUnboundLocalVariable
                uri_prompt = original_prompt
            except UnboundLocalError:
                continue

    # Get output directory
    if get_output:
        dir_prompt = "[OPTIONAL] Enter path to output dir: "
        while (output_dir := input(dir_prompt)) and not path.isdir(output_dir):
            print(f"Couldn't find directory '{output_dir}'")

        return urls, output_dir
    return urls


def main():
    """Main entry point."""

    urls, output = ApplicationArgParser(
        description="Download book as pdf from hanser-elibrary.com"
    ).validate_application_args()

    if not urls:
        if not output:
            urls, output = get_console_input()
        else:
            urls = get_console_input(get_output=False)

    for book in urls:
        app = Application(book, output)
        app.run()


if __name__ == '__main__':
    main()
