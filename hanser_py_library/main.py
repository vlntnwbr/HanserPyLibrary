"""
This tool downloads each chapter of a book from hanser-elibrary.com and
merges them into a single PDF File.

:copyright: (c) 2019 by Valentin Weber
:license: GNU General Public License Version 3, see LICENSE
"""

from collections import namedtuple
from getpass import getuser
from os import path, mkdir
from io import BytesIO

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger
from requests import get

Chapter = namedtuple("Chapter", ["title", "href"])


class Application(object):
    """Application class."""

    BASE_URL = "https://www.hanser-elibrary.com"

    def __init__(self, url: str, output_dir: str = ""):
        self.url = url
        self.title = ""  # Book title
        self.authors = []  # List of authors
        self.chapter_list = []  # Chapter: URL
        self.chapters = []  # Contains downloaded PDFs
        self.book = PdfFileMerger()  # Merged Book

        if not output_dir:
            user = path.expanduser("~" + getuser())
            self.output_dir = path.join(
               user, "Documents", "HanserPyLibrary"
            )

        else:
            self.output_dir = output_dir

    def run(self):
        """Starts and exists the application."""

        self.get_book_info()
        self.download_book()
        self.merge_pdf()
        self.save_book()
        exit_script("Download and Merge complete.")

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

    def save_book(self):
        """Save merged PDF."""

        if len(self.book.pages) > 0:

            filename = self.title + ".pdf"

            if not path.isdir(self.output_dir):
                print("Creating '" + self.output_dir + "'")
                mkdir(self.output_dir)

            print("Saving '" + filename + "' to '" + self.output_dir + "'")
            self.book.write(path.join(self.output_dir, filename))
            print("Saving successful.\n")
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


def get_user_input():
    """Ask user for input URL and output_dir."""

    uri_prompt = "Enter URI for 'hanser-elibrary.com' book: "
    while not (url := input(uri_prompt)).startswith(Application.BASE_URL):
        uri_prompt = "Please enter a valid URI: "

    dir_prompt = "[OPTIONAL] Enter path to output dir: "
    while (output_dir := input(dir_prompt)) and not path.isdir(output_dir):
        print("Couldn't find directory '" + output_dir + "'")
    print()
    return url.strip(), output_dir.strip()


def exit_script(message: str, code: int = 0):
    """Display error and wait for input to exit script"""

    if code:
        message = "\n" + "ERROR: " + message

    print(message)
    input("Press ENTER to exit ")
    exit(code)


def main():
    """Main entry point."""

    book, output = get_user_input()

    app = Application(book, output)
    app.run()


if __name__ == '__main__':
    main()
