"""Main entry point for hanser-py-library"""


from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
import os
import sys

from typing import List, Tuple
from urllib.parse import urlparse, urljoin

from .import PROG_DESC, PROG_NAME
from .core.exceptions import AccessError, DownloadError, MetaError, MergeError
from .core.utils import HANSER_URL, is_isbn, log, log_download
from .hanser import BookParser, DownloadManager


class MainParser(ArgumentParser):
    """ArgumentParser for hanser-py-library"""

    def __init__(self) -> None:

        example_url = urljoin(HANSER_URL, "/isbn/9783446450523")
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
            metavar="",
            help="Path to output path. Cannot point to file.",
            type=self.is_valid_dir_path,
            default=os.getcwd()
        )

        self.add_argument(
            "-f", "--force",
            action="store_true",
            help="Set this to force creation of path to output dir",
            dest="force_dir"
        )

        self.add_argument(
            "--isbn",
            metavar="",
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
            if "-" in isbn:
                isbn = isbn.replace("-", "")
            if not is_isbn(isbn):
                raise ArgumentTypeError(f"Invalid ISBN checksum for '{isbn}'")
            return urljoin(HANSER_URL, "/".join(["isbn", isbn]))
        return isbn

    @staticmethod
    def is_application_url(url: str) -> str:
        """Check if URL is valid url for hanser-elibrary.com"""

        hanser_url = urlparse(HANSER_URL)
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

        if (elements := len(path_list)) != 2 and elements != 4:  # noqa pylint: disable=used-before-assignment
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
    """Entry point as specified by PROG_NAME"""

    args = MainParser()
    urls, dest, force = args.validate()
    log("", "Starting hanser-py-library", 0)
    try:
        app = DownloadManager(HANSER_URL, dest, force)
    except PermissionError:
        log("exit", f"Could not create output dir {dest}", 1)
        sys.exit(1)
    for url in urls:
        try:
            log("info", f"Looking for book @ {url}")
            search = BookParser(url)
            book = search.make_book()
            log("found book", f"{str(book)}")
            if book.complete_available:
                log("info", "Complete Book PDF is available")
                log("download", book.title)
                book.contents = app.download_book(book.complete_available)
            else:
                for i, chapter in enumerate(book.chapters):
                    log_download(i + 1, chapter.title, len(book.chapters))
                    book.chapters[i] = app.download_chapter(chapter)
            log("info", f"Collecting '{book.title}'...")
            result = app.write_book(book)
            log("info", f"Saved book as {result}", 1)
        except (AccessError, DownloadError, MetaError, MergeError) as exc:
            err_msg = "Skipped " + url + "\n{}"
            log("error", err_msg.format(exc.args[0]), 0)
        except KeyboardInterrupt:
            log("exit", "Operation cancelled by user", 1)
            sys.exit(1)
    log("finished", "exiting hanser-py-library", 1)


if __name__ == '__main__':
    main()
