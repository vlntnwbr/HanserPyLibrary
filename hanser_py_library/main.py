"""
This tool downloads each chapter of a merger from hanser-elibrary.com and
merges them into a single PDF File.

:copyright: (c) 2019 by Valentin Weber
:license: GNU General Public License Version 3, see LICENSE
"""

from argparse import ArgumentParser, ArgumentTypeError, HelpFormatter
from collections import namedtuple
from io import BytesIO
from os import path, mkdir
import sys
from typing import List, Tuple

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger
from requests import get

Chapter = namedtuple("Chapter", ["title", "href"])
ApplicationArgs = Tuple[List[str], str, bool]


# TODO Update README.md
class Application(object):
    """Application class."""

    HANSER_URL = "https://www.hanser-elibrary.com"

    def __init__(self, output_dir: str, force_dir: bool = False):
        self.pdf_list = []  # Contains downloaded PDFs
        self.merger = PdfFileMerger()  # Merged Book

        if not output_dir:
            self.force_dir = True
            self.output_dir = path.join(
                path.expanduser("~"), "Documents", "HanserPyLibrary"
            )
        else:
            self.output_dir = output_dir.strip()
            self.force_dir = force_dir

    def hanser_download(self, url: str):
        """Get title, authors and chapters and check authorization."""

        response = get(url.strip())
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
        self.merge_pdf(pdf_list, title)
        self.write_pdf(title)

    # TODO Merge methods merge_pdf() and write_pdf()
    def merge_pdf(self, pdf_list: List[BytesIO], title: str):
        """Merges all PDFs in pdf_list into one PDF file."""

        if not pdf_list:
            sys.exit("No PDFs to merge.")

        print("Start Merging '" + title + "'")
        for pdf in pdf_list:
            self.merger.append(pdf)
        print("Merge Complete.\n")

    def write_pdf(self, filename: str):
        """Save merged PDF."""

        if len(self.merger.pages) > 0:
            filename = safe_filename(filename)

            if not path.isdir(self.output_dir) and self.force_dir:
                print("Creating '" + self.output_dir + "'")
                mkdir(self.output_dir)

            print("Saving '" + filename + "' to '" + self.output_dir + "'")
            self.merger.write(path.join(self.output_dir, filename))
            print("Done.\n")
            self.merger = PdfFileMerger()
        else:
            sys.exit("No merger to save.")

    @staticmethod
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
            conflict_handler=parser_args.get("conflict_handler", "error"),
            add_help=parser_args.get("add_help", True),
            allow_abbrev=parser_args.get("allow_abbrev", True)
        )

        self.url = self.ParserArgFlags("-u", "--url")
        self.out = self.ParserArgFlags("-o", "--out")
        self.force = self.ParserArgFlags("-fo", "--force")

        self.add_application_args()
        self.application_args = self.parse_args()

    def add_application_args(self):
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
        if url and not url.startswith(Application.HANSER_URL):
            msg = f"'{url}' doesn't start with '{Application.HANSER_URL}'"
            raise ArgumentTypeError(msg)
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


# TODO make this an Application static method
def safe_filename(name: str):
    """Remove most non-alnum chars from string and add '.pdf'"""
    return "".join(c for c in name if c.isalnum() or c in "- ._").strip() + ".pdf"


def get_console_input(get_output: bool = True) -> ApplicationArgs or List[str]:
    """Get at least one URL and an optional output_dir if needed."""

    # Get List of URLs
    multiple_urls = "y"
    urls = []
    while multiple_urls == "y":
        uri_prompt = "Enter URI for 'hanser-elibrary.com' merger: "
        while not (url := input(uri_prompt)).startswith(Application.HANSER_URL):
            # original_prompt = uri_prompt
            uri_prompt = "Please enter a valid URI: "

        urls.append(url)
        multiple_urls = input("Add another merger ? (y) ").lower()

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


def main():
    """Main entry point."""

    urls, output, force = ApplicationArgParser(
        description="Download merger as pdf from hanser-elibrary.com"
    ).validate_application_args()

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
