<!--- Copyright (c) 2020 Valentin Weber

This file is part of hanser-py-library.

hanser-py-library is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

hanser-py-library is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with hanser-py-library. If not, see <https://www.gnu.org/licenses/#GPL>.
--->

# hanser-py-library ![](https://github.com/vlntnwbr/hanserpylibrary/workflows/Tests/badge.svg)

This tool downloads a book from *<https://www.hanser-elibrary.com>*  saves them
to a PDF File called *<Book Title>-<Year>.pdf*. If the book's title contains
characters that aren't allowed in a filename it will be saved as
*<Book ISBN>-<Year>.pdf*. If files with that name already exist the number of
existing files will be appended to the chosen file name like this *<filename> (#)*.

By default the merged book will be saved in the directory from which the
program was called, but you can provide a custom output directory.

If a complete book pdf is available, the tool will preferably download that
file, otherwise it will download each individual chapter and merge them into a
single file before saving. Unfortunately, this leads to links within the merged
book (e.g. chapter references) being broken.

The tool will check whether you are authorized to access the book before
downloading anything. If you are unauthorized, the book will be skipped.

## Installation
Installing through [pipx][1] isolates packages in their own environment and
exposes their entrypoints via PATH.
```
pipx install hanser-py-library
```
Alternatively install regularly via pip: 
```
pip install hanser-py-library
```

## Usage
```
usage: hanser [-h] [--isbn [[...]]] [-o PATH] [-f] [URL [URL ...]]
```

You must provide at least one valid URL or ISBN. The program will attempt
to fix URLs with missing schemes by defaulting to "https://". Each URL
needs to end with a valid ISBN-10 or -13 number. Valid URL formats include:

**Referencing by ISBN-10 or ISBN-13**
```
https://www.hanser-elibrary.com/isbn/{ISBN}
https://hanser-elibrary.com/isbn/{ISBN}
www.hanser-elibrary.com/isbn/{ISBN}
hanser-elibrary.com/isbn/{ISBN}
```

**Referencing by DOI and ISBN-13**
```
https://www.hanser-elibrary.com/doi/book/{DOI}/{ISBN}
https://hanser-elibrary.com/doi/book/{DOI}/{ISBN}
www.hanser-elibrary.com/doi/book/{DOI}/{ISBN}
hanser-elibrary.com/doi/book/{DOI}/{ISBN}
```

### Options
| **Short** | **Long** | **Description** |
| :-: | :-: | :-- |
| -h | --help | Show help message and exit. |
| -o | --out | Path to output directory. Relative and abstract paths supported. Cannot point towards file. <br> Paths starting with '~' it will be expanded from the user's home directory <br> Path must point towards existing directory unless `-f` is set.|
| -f | --force | If set the output directory and every directory on the way will be forcibly created. <br> Exits if the directory cannot be created. |
|    | --isbn | ISBNs of books to download. Can be either ISBN-10 or 13. <br> If you want to provide both ISBNs and URLs, provide URLs first like this: <br> `hanser [URL [URL ...]] [--isbn [[...]]]`<br> If ISBN(s) and URL(s) are provided, URL books will be downloaded before ISBN books.|

### Examples
#### Saving in current working directory
```
hanser https://www.hanser-elibrary.com/isbn/9783446450776

hanser https://www.hanser-elibrary.com/doi/book/10.3139/9783446450776

hanser --isbn 9783446450776
```
#### Saving in a directory that exists
```
hanser -o path/to/dir hanser-elibrary.com/isbn/9783446450776
```

#### Saving in a directory that may or may not exist
```
hanser -o path/to/dir -f hanser-elibrary.com/isbn/9783446450523
```

## Encountered a Bug?
Feel free to [open an issue][new-issue] if you encountered bugs or have other
ideas that aren't yet listed in the [backlog][issues].

[1]: https://github.com/pipxproject/pipx
[new-issue]: https://github.com/vlntnwbr/HanserPyLibrary/issues/new/choose
[issues]: https://github.com/vlntnwbr/HanserPyLibrary/issues
