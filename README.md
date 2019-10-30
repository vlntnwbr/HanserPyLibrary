# Hanser PyLibrary

This tool downloads each chapter of a book from https://www.hanser-elibrary.com
and merges them into a single PDF File called *{Booktitle}.pdf*. Unfortunately,
as of right now it seems like  links within the merged book (e.g. chapter 
references) do not work.

The tool will check whether you are authorized to download the book before
downloading anything. If you are unauthorized, the program will exit.

By default the book will be saved in ~/{user}/Documents/HanserPyLibrary, but
you can provide a custom output directory. If either directory, custom or 
default, does not exist it will be created. You cannot provide a custom
output filename.

Planned updates:
1. Allow custom output filename
2. Creating the custom output dictionary will become optional
3. Add argument parsing for use with command line
4. Fix links within merged PDF. Maybe.