from setuptools import setup

setup(
    name="pynetinstall",
    version="1.0",
    description="Module to perform Mikrotik Routerboard Netinstall via Etherboot",
    url="https://github.com/dvtirol/pynetinstall",
    author="Daten-Verarbeitung-Tirol GmbH",
    author_email="netz@tirol.gv.at",
    packages=["pynetinstall", "pynetinstall.plugins"],
    package_data={'pynetinstall': ['logging.ini']},
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Operating System :: POSIX :: Linux",
        "Intended Audience :: System Administrators",
    ],
    entry_points={
        "console_scripts": ["pynetinstall = pynetinstall.__main__"]
    }
)
