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

"""Setup script."""

import subprocess
from os import path
from typing import List, TextIO

from setuptools import find_packages, setup

from hanser_py_library import MAIN_NAME, MAIN_DESC

REQUIREMENTS_TXT = "requirements.txt"
HEREDIR = path.abspath(path.dirname(__file__))

PROG = "hanser-py-library"
VERSION = "0.3.4"
GITHUB = "https://github.com/vlntnwbr/HanserPyLibrary"


def open_local(filename: str, mode: str = "r") -> TextIO:
    """Open file in this directory."""

    return open(path.join(HEREDIR, filename), mode)


def execute_command(args: List[str]) -> List[str]:
    """Execute external command and return stdout as list of strings."""

    try:
        process = subprocess.run(
            args,
            capture_output=True,
            check=True,
            text=True
        )
        return [line.strip() for line in process.stdout.splitlines()]
    except subprocess.CalledProcessError:
        return []


def create_requirements_txt() -> None:
    """Create file 'requirements.txt' from 'Pipfile.lock'."""

    try:
        with open_local("Pipfile.lock"):
            pass
    except FileNotFoundError:
        return

    pipenv_lines = execute_command(["pipenv", "lock", "-r"])
    if not pipenv_lines:
        return

    lines = [line for line in pipenv_lines[1:] if line]
    with open_local(REQUIREMENTS_TXT, "w") as req_file:
        req_file.write("### DO NOT EDIT! This file was generated.\n")
        req_file.write("\n".join(lines))
        req_file.write("\n")


def read_requirements() -> List[str]:
    """Read lines of requirements.txt and return them as list"""

    with open_local(REQUIREMENTS_TXT) as file:
        return [
            line.strip() for line in file.readlines()
            if line and not line.startswith("#") and not line.startswith("-i")
        ]


if __name__ == '__main__':
    create_requirements_txt()
    INSTALL_REQUIRES = read_requirements()
    README = open_local("README.md").read()
    setup(
        name=PROG,
        description=MAIN_DESC,
        long_description=README,
        long_description_content_type="text/markdown",
        version=VERSION,
        packages=find_packages(),
        include_package_data=True,
        python_requires=">=3.8",
        install_requires=INSTALL_REQUIRES,
        license="GNU GPLv3",
        url=GITHUB,
        author="Valentin Weber",
        author_email="dev@vweber.eu",
        maintainer="Valentin Weber",
        maintainer_email="dev@vweber.eu",
        project_urls={"Bug Tracker": GITHUB + "/issues?q=label%3bug"},
        entry_points={'console_scripts': [
            MAIN_NAME + " = hanser_py_library.entrypoints.hanser:main"
        ]},
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Console",
            "Intended Audience :: Education",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: GNU Affero General Public License v3",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3 :: Only",
            "Topic :: Education",
            "Topic :: Scientific/Engineering",
            "Topic :: Utilities"
        ]
    )
