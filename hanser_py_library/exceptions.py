"""Exceptions for hanser-py-library"""


class AccessError(Exception):
    """Raised when no-access icon is visible on book page"""


class MetaError(Exception):
    "Error that occurs while parsing website for the book"


class MergeError(Exception):
    """Error that occurs while merging the book"""


class DownloadError(Exception):
    """Exception that occurs while the book is downloaded"""
