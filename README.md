# Tyora: mooc.fi CSES exercise task CLI
[![PyPI - Version](https://img.shields.io/pypi/v/tyora?pypiBaseUrl=https%3A%2F%2Ftest.pypi.org&logo=pypi&label=pypitest)](https://test.pypi.org/project/tyora/)
[![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fmadeddie%2Ftyora%2Fmain%2Fpyproject.toml&logo=python)](https://github.com/madeddie/tyora/blob/main/pyproject.toml#L15)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/madeddie/tyora/ci.yml)](https://github.com/madeddie/tyora/actions/workflows/ci.yml)
[![GitHub License](https://img.shields.io/github/license/madeddie/tyora)](https://github.com/madeddie/tyora/blob/main/LICENSE)


This script interacts with the mooc.fi instance of the CSES (https://cses.fi) website to perform various actions such as logging in, retrieving exercise lists, and submitting solutions.
It provides a convenient way to view and submit tasks.

## Features

- **Login**: Log in to your CSES account using username and password.
- **Retrieve Exercise Lists**: Get a list of exercises available on the CSES platform.
- **Submit Solutions**: Submit your solutions to specific exercises on the platform.

## Installation

   ```bash
   pip install tyora
   ```

## Usage

The script can be used from the command line. The following commands are available:

- `tyora login`: Stores your mooc.fi username and password and tests if we can log in with them.
- `tyora list`: Retrieves and displays a list of exercises available on the CSES platform.
- `tyora show <exercise_id>`: Displays the details of a specific exercise.
- `tyora submit <exercise_id> <path_to_solution_file>`: Submits a solution to a specific exercise.

## Origin of name

The name "tyora" is derived from Finnish words: "työ" meaning "work" and "pyörä" meaning "wheel".
Anyway, `pyora` was already taken, so I went with `tyora`... ;)

## Contributing

Contributions are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request.

**Rye**

This project uses [Rye](https://rye-up.com/) to manage dependencies, formatting, linting and packaging.
Install it using the instructions on the Rye website, then run `rye sync` in the root of the project to install the necessary tools.

**How to use Rye**

Reading the documentation is probably a good idea, but in short:

- `rye sync` installs the necessary tools.
- `rye format` formats the code.
- `rye lint` lints the code.

**pre-commit**

We use pre-commit to run the linters before each commit. To install it, run `rye sync` and `rye run pre-commit install`.
This is not strictly required, but it'll make your life easier by catching issues before the github actions deny your PR.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
