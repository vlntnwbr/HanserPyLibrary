# hanser-py-library ![](https://github.com/vlntnwbr/hanserpylibrary/workflows/Tests/badge.svg)

This tool downloads each chapter of a book from *<https://www.hanser-elibrary.com>* 
and merges them into a single PDF File called *{Booktitle}.pdf*. If the
book's title contains characters that aren't allowed in a filename it
will be saved as *{ISBN}.pdf*.

Unfortunately, it seems like links  within the merged book (e.g.
chapter references) do not work.

The tool will check whether you are authorized to access the book before
downloading anything. If you are unauthorized, the book will be skipped.

By default the merged book will be saved in the directory from which the
program was called, but you can provide a custom output directory.

You cannot yet provide a custom output filename.

## Installation
Installing through [pipx][1] isolates packages in their own environment and
exposes their entrypoints via PATH.
```
pipx install https://github.com/vlntnwbr/HanserPyLibrary/releases/latest/download/hanser-py-library.tar.gz
```
Alternatively install regularly via pip: 
```
pip install https://github.com/vlntnwbr/HanserPyLibrary/releases/latest/download/hanser-py-library.tar.gz
```

## Usage
```
hanser [-h] [-o] [-f] [--isbn [[...]]] [URL [URL ...]]
```

You must provide at least one valid URL or ISBN. The program will attempt
to fix URLs with missing schemes by defaulting to "https://". Each URL
needs to end with a valid ISBN-13 number. Valid URL formats include:

**Referencing by ISBN-10 or ISBN-13**
* https://www.hanser-elibrary.com/isbn/{ISBN}
* https://hanser-elibrary.com/isbn/{ISBN}
* www.hanser-elibrary.com/isbn/{ISBN}
* hanser-elibrary.com/isbn/{ISBN}

**Referencing by DOI and ISBN-13**
* https://www.hanser-elibrary.com/doi/book/{DOI}/{ISBN}
* https://hanser-elibrary.com/doi/book/{DOI}/{ISBN}
* www.hanser-elibrary.com/doi/book/{DOI}/{ISBN}
* hanser-elibrary.com/doi/book/{DOI}/{ISBN}

### Options
| **Short** | **Long** | **Description** |
| :-: | :-: | :-- |
| -h | --help | Show help message and exit. |
| -o | --out | Path to output directory. Relative and abstract paths supported. Cannot point towards file. <br> Paths starting with '~' it will be expanded from the user's home directory <br> Path must point towards existing directory unless `-f` is set.|
| -f | --force | If set the output directory and every directory on the way will be forcibly created. <br> Exits if the directory cannot be created. |
|    | --isbn | ISBN(s) of books(s) to download. Can be either ISBN-10 or 13. <br> If ISBN(s) and URL(s) are provided, ISBN books will be downloaded before URL books. |

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

[1]: https://github.com/pipxproject/pipx