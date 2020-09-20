"""
This tool downloads each chapter of a book from hanser-elibrary.com and
merges them into a single PDF File.

:copyright: (c) 2019 by Valentin Weber
:license: GNU General Public License Version 3, see LICENSE
"""

from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
import os
from typing import List, Tuple
from urllib.parse import urlparse, urljoin

from . import PROG_NAME, PROG_DESC
from .utils import is_isbn


class HanserParser(ArgumentParser):
    """ArgumentParser for hanser-py-library."""

    HANSER_URL = "https://www.hanser-elibrary.com"

    def __init__(self) -> None:

        example_url = urljoin(self.HANSER_URL, "/isbn/9783446450523")
        usage_examples = "EXAMPLES:\n" + "\n".join((
            f"{PROG_NAME} {example_url}",
            f"{PROG_NAME} -o /existing_dir {example_url}",
            f"{PROG_NAME} -o /dir/to/create -f {example_url} "
        ))

        super().__init__(
            prog=PROG_NAME,
            description=PROG_DESC,
            epilog=usage_examples,
            formatter_class=RawTextHelpFormatter,
        )

        self.add_args()

    def add_args(self) -> None:
        """Add arguments url, isbn, out and force to parser"""

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

    def validate(self) -> Tuple[List[str], str, bool]:
        """Returns urls, output_dir and force_dir from parsed args"""

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
                raise ArgumentTypeError(f"Invalid ISBN checksum for '{isbn}'")
            return urljoin(HanserParser.HANSER_URL, "/".join(["isbn", isbn]))
        return isbn

    @staticmethod
    def is_application_url(url: str) -> str:
        """Check if URL is valid url for hanser-elibrary.com"""

        hanser_url = urlparse(HanserParser.HANSER_URL)
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
        """Expands user/abstract paths and fails if it leads to file"""

        if path.startswith("~"):
            path = os.path.normpath(os.path.expanduser(path))

        if path.startswith("."):
            path = os.path.abspath(path)

        if os.path.isfile(path):
            raise ArgumentTypeError(f"'{path}' points to a file")
        return path


def main() -> None:
    """Main entry point."""

    args = HanserParser()
    urls, dest, force = args.validate()
    print(dest, force)
    for url in urls:
        print(" " * 4 + url)


if __name__ == '__main__':
    main()
