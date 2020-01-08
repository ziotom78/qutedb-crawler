# QuteDB-crawler

This Python program walks into a structure of folders containing Qubic test
files (created by QubicStudio) and create thumbnails and metadata JSON files
for each of them.

## How to install and run the program

You must use [poetry](https://python-poetry.org/) to install dependencies and
run the program. Run

    git clone https://github.com/ziotom/qutedb-crawler
	cd qutedb-crawler
	poetry install

This will create a virtual environment and install all the dependencies. To get
help about how to run the program, execute the following line within the
`qutedb-crawler` directory:

	poetry run qutedb-crawler --help

The only mandatory argument is the root path to be scanned.

## License

This script is released under a MIT license.
