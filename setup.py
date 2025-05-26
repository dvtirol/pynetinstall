from setuptools import setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="pynetinstall",
    version="1.1.0",
    description="Module to perform Mikrotik Routerboard Netinstall via Etherboot",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/dvtirol/pynetinstall",
    author="Daten-Verarbeitung-Tirol GmbH",
    author_email="netz@tirol.gv.at",
    packages=["pynetinstall", "pynetinstall.plugins"],
    package_data={'pynetinstall': ['logging.ini']},
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={
        "console_scripts": ["pynetinstall = pynetinstall.__main__"]
    }
)
