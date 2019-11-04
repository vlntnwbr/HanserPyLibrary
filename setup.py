"""Setup script"""

from os import path
from setuptools import find_packages, setup

VERSION = "0.0.1"
README = "README.md"
REQUIREMENTS = "requirements.txt"
HEREDIR = path.abspath(path.dirname(__file__))


def read_local(filename: str, mode: str = "") -> str or list:
    """Read contents of a file in this directory"""

    with open(path.join(HEREDIR, filename), "r") as file:
        if mode == "rl":
            content = [line.strip() for line in file.readlines() if line]
        else:
            content = file.read()
    return content


if __name__ == '__main__':

    setup(
        name="hanser-py-library",
        description="Download & merge each PDF of a book from Hanser Library",
        long_description=read_local(README),
        version=VERSION,
        packages=find_packages(),
        include_package_data=True,
        python_requires=">=3.8",
        install_requires=read_local(REQUIREMENTS, "rl"),
        license="GNU GPLv3",
        url="https://github.com/vlntnwbr/HanserPyLibrary",
        maintainer="Valentin Weber",
        maintainer_email="dev@example.com",
        entrypoints={
            'console-scripts': [
                "hanser-py-library = hanser_py_library.main:main"
            ]
        }
    )
