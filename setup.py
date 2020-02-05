"""Setup script."""

import subprocess
from os import path
from typing import List, TextIO

from setuptools import find_packages, setup

from hanser_py_library import PROG_NAME, PROG_DESC

VERSION = "0.0.5"
REQUIREMENTS_TXT = "requirements.txt"
HEREDIR = path.abspath(path.dirname(__file__))


def open_local(filename: str, mode: str = "r") -> TextIO:
    """Open file in this directory."""

    return open(path.join(HEREDIR, filename), mode)


def execute_command(args: List[str]) -> List[str]:
    """Execute external command and return stdout as list of strings."""

    try:
        process = subprocess.run(args, stdout=subprocess.PIPE, check=True)
        return [
            line.strip() for line in process.stdout.decode("utf-8").split("\n")
        ]
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
        return [line.strip() for line in file.readlines()
                if line and not line.startswith("#")]


if __name__ == '__main__':
    create_requirements_txt()
    README = open_local("README.md").read()
    INSTALL_REQUIRES = read_requirements()

    setup(
        name="hanser-py-library",
        description=PROG_DESC,
        long_description=README,
        version=VERSION,
        packages=find_packages(),
        include_package_data=True,
        python_requires=">=3.8",
        install_requires=INSTALL_REQUIRES,
        license="GNU GPLv3",
        url="https://github.com/vlntnwbr/HanserPyLibrary",
        maintainer="Valentin Weber",
        maintainer_email="dev@example.com",
        entry_points={'console_scripts': [
            PROG_NAME + " = hanser_py_library.main:main"
        ]})
