# Hanser PyLibrary

This tool downloads each chapter of a book from https://www.hanser-elibrary.com
and merges them into a single PDF File called *{Booktitle}.pdf*. Unfortunately,
as of right now it seems like links within the merged book (e.g. chapter 
references) do not work.

The tool will check whether you are authorized to access the book before
downloading anything. If you are unauthorized, the program will exit.

By default the book will be saved in ~/{user}/Documents/HanserPyLibrary, but
you can provide a custom output directory. The default directory will always
be created if it doesn't exist, while forcibly creating a custom directory is
optional. You cannot yet provide a custom output filename.

## Usage
`py -m hanser_py_library.main [OPTIONS]`

*  *If no OPTIONS are provided or an URL is missing, there will be input 
    prompts to add at least one valid URL*
*  *If two different paths are supplied for -o and -fo the program will exit.*

### Options
| **Short** | **Long** | **Description** |
| :-: | :-: | :-- |
| -h | --help | Show help message and exit program. |
| -u | --url | List of URLs pointing towards book to download. |
| -o | --out | Output directory that already exists. If it doesnt, the program exits. |
| -fo | --force | Output directory that will be created if it doesn't exist. If path points to a file, the program exits. |

### Examples
`py -m hanser_py_library.main -u https://www.hanser-elibrary.com/isbn/978344645052`

`py -m hanser_py_library.main -u https://www.hanser-elibrary.com/isbn/9783446450523 -o path/to/existing_dir`

`py -m hanser_py_library.main -u https://www.hanser-elibrary.com/isbn/9783446450523 -fo path/to/nonexistent_dir`

## Planned updates
1.  Improve Error handling
2.  Implement Caching of already downloaded chapters
3.  Allow custom output filename
4.  Fix links within merged PDF. Maybe.
