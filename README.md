# Hanser PyLibrary

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
`pip install https://github.com/vlntnwbr/HanserPyLibrary/archive/master.zip`

*  Make sure you have Python Version 3.8 or greater
*  Make sure the Python/Scripts folder is part of your PATH variables
*  Make sure you have pipenv installed

## Usage
`hanser [OPTIONS] URL(s) [URL, ...]`

You must provide at least one valid URL. The program will attempt to
fix URLs with missing schemes by defaulting to "https://". Each URL
needs to end with a valid ISBN-13 number. Valid URL formats include:

**Referencing by ISBN-10 or ISBN-13**
* https://www.hanser-elibrary.com/isbn/\<ISBN>
* https://hanser-elibrary.com/isbn/\<ISBN>
* www.hanser-elibrary.com/isbn/\<ISBN>
* hanser-elibrary.com/isbn/\<ISBN>

**Referencing by DOI and ISBN-13**
* https://www.hanser-elibrary.com/doi/book/\<DOI>/\<ISBN>
* https://hanser-elibrary.com/doi/book/\<DOI>/\<ISBN>
* www.hanser-elibrary.com/doi/book/\<DOI>/\<ISBN>
* hanser-elibrary.com/doi/book/\<DOI>/\<ISBN>

### Options
| **Short** | **Long** | **Description** |
| :-: | :-: | :-- |
| -h | --help | Show help message and exit program. |
| -o | --out | Path to output directory. Relative and abstract paths supported. Cannot point towards file. <br> If the path starts with '~' it will be expanded from the user's home directory |
| -f | --force | If set the output directory and every directory on the way will be forcibly created. |

### Examples
#### Saving in current working directory

`hanser https://www.hanser-elibrary.com/isbn/9783446450776`

`hanser https://hanser-elibrary.com/isbn/9783446450776`

`hanser www.hanser-elibrary.com/isbn/9783446450776`

`hanser hanser-elibrary.com/isbn/9783446450776`

`hanser https://www.hanser-elibrary.com/doi/book/10.3139/9783446450776`

`hanser https://hanser-elibrary.com/doi/book/10.3139/9783446450776`

`hanser www.hanser-elibrary.com/doi/book/10.3139/9783446450776`

`hanser hanser-elibrary.com/doi/book/10.3139/9783446450776`

All following examples will work with all of the URLs listed above.

#### Saving in a directory that exists
`hanser -o path/to/dir hanser-elibrary.com/isbn/9783446450776`

#### Saving in a directory that may or may not exist
`hanser -o path/to/dir -f hanser-elibrary.com/isbn/9783446450523`
