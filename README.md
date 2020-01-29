# Hanser PyLibrary

This tool downloads each chapter of a book from *https://www.hanser-elibrary.com* 
and merges them into a single PDF File called *{Booktitle}.pdf*. 

Unfortunately, it seems like links  within the merged book (e.g.
chapter references) do not work.

The tool will check whether you are authorized to access the book before
downloading anything. If you are unauthorized, the program will exit.

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
needs to end with a valid ISBN-13 number.

### Options
| **Short** | **Long** | **Description** |
| :-: | :-: | :-- |
| -h | --help | Show help message and exit program. |
| -o | --out | Path to output directory. Cannot point towards file. <br> If the path starts with '~' it will be expanded from the user's home directory |
| -f | --force | If set the output directory and every directory on the way will be forcibly created. |

### Examples
Save the book in the current working directory

`hanser -u https://www.hanser-elibrary.com/isbn/978344645052`

Save the book in a directory which exists

`hanser -u https://www.hanser-elibrary.com/isbn/9783446450523 -o path/to/dir`

Save the book to a directory that may or may not exist

`hanser-py-library -u https://www.hanser-elibrary.com/isbn/9783446450523 -o path/to/dir -f`
