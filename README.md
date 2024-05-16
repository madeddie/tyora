# Tyora: mooc.fi CSES exercise task CLI
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/madeddie/tyora/test.yml)](https://github.com/madeddie/tyora/actions)

This script interacts with the mooc.fi instance of the CSES (https://cses.fi) website to perform various actions such as logging in, retrieving exercise lists, and submitting solutions.
It provides a convenient way to view and submit tasks.

## Features

- **Login**: Log in to your CSES account using username and password.
- **Retrieve Exercise Lists**: Get a list of exercises available on the CSES platform.
- **Submit Solutions**: Submit your solutions to specific exercises on the platform.

## Installation

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/madeddie/tyora.git
   ```

2. Navigate to the project directory:

   ```bash
   cd tyora
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Configure the script by running:

   ```bash
   python tyora.py configure
   ```

   Follow the prompts to enter your mooc.fi username and password. This information will be stored for future use.

2. List available exercises:

   ```bash
   python tyora.py list
   ```

   This will retrieve and display a list of exercises available on the CSES platform.

3. Submit a solution:

   ```bash
   python tyora.py submit <exercise_id> <path_to_solution_file>
   ```

   Replace `<exercise_id>` with the ID of the exercise you want to submit a solution for, and `<path_to_solution_file>` with the path to your solution file.

## Origin of name

The name "tyora" is derived from Finnish words: "työ" meaning "work" and "pyörä" meaning "wheel".
Anyway, `pyora` was already taken, so I went with `tyora`... ;)

## Contributing

Contributions are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
