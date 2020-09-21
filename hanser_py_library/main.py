"""Main entry point for hanser-py-library"""

import sys

from .cli import MainParser
from .exceptions import AccessError, DownloadError, MetaError, MergeError
from .hanser import BookParser, DownloadManager
from .utils import HANSER_URL, log, log_download


def main() -> None:
    """Entry point as specified by PROG_NAME"""

    args = MainParser()
    log("", "Starting hanser-py-library", 0)
    urls, dest, force = args.validate()
    try:
        app = DownloadManager(HANSER_URL, dest, force)
    except PermissionError:
        log("exit", f"Could not create output dir {dest}", 1)
        sys.exit(1)
    for url in urls:
        try:
            search = BookParser(url)
            err_msg = "Skipped ISBN " + search.isbn + "\n{}"
            log("info", f"Looking for book with ISBN {search.isbn}")
            book = search.make_book()
            log("info", f"Found '{book.title}' by {book.authors} "
                f"with {len(book.chapters)} chapters")
            for i, chapter in enumerate(book.chapters):
                log_download(i + 1, chapter.title, len(book.chapters))
                book.chapters[i] = app.download_chapter(chapter)
            log("info", f"Collecting '{book.title}'...")
            result = app.write_book(book)
            log("info", f"Saved book as {result}", 1)
        except (AccessError, DownloadError, MetaError, MergeError) as exc:
            log("error", err_msg.format(exc.args[0]), 0)
        except KeyboardInterrupt:
            log("exit", "Operation cancelled by user", 1)
            sys.exit(1)
    log("finished", "exiting hanser-py-library", 1)


if __name__ == '__main__':
    main()
