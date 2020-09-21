"""Exceptions for hanser-py-library"""


class AccessError(Exception):
    """Raised when no-access icon is visible on book page"""


class MetaError(Exception):
    "Raised on error during search for book information"


class MergeError(Exception):
    """Raised on error while merging or saving the book"""


class DownloadError(Exception):
    """Raised on error during download of a book chapter"""
