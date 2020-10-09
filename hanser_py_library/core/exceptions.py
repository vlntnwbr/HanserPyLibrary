##
#   Copyright (c) 2020 Valentin Weber
#
#   This file is part of hanser-py-library.
#
#   hanser-py-library is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   hanser-py-library is distributed in the hope that it will be
#   useful, but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with hanser-py-library. If not, see
#   <https://www.gnu.org/licenses/#GPL>.
##

"""Exceptions for hanser-py-library"""


class AccessError(Exception):
    """Raised when no-access icon is visible on book page"""


class MetaError(Exception):
    "Raised on error during search for book information"


class MergeError(Exception):
    """Raised on error while merging or saving the book"""


class DownloadError(Exception):
    """Raised on error during download of a book chapter"""
