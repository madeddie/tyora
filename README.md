# mooc.fi CSES exercise task cli
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/madeddie/moocfi_cses/test.yml)


This script interacts with the mooc.fi instance of the CSES (Competitive Programmer's Handbook) website to perform various actions such as logging in, retrieving exercise lists, and submitting solutions. It provides a convenient way to view and submit tasks.

## Features

- **Login**: Log in to your CSES account using username and password.
- **Retrieve Exercise Lists**: Get a list of exercises available on the CSES platform.
- **Submit Solutions**: Submit your solutions to specific exercises on the platform.

## Installation

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/madeddie/moocfi_cses.git
   ```

2. Navigate to the project directory:

   ```bash
   cd moocfi_cses
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Configure the script by running:

   ```bash
   python moocfi_cses.py configure
   ```

   Follow the prompts to enter your mooc.fi username and password. This information will be stored for future use.

2. List available exercises:

   ```bash
   python moocfi_cses.py list
   ```

   This will retrieve and display a list of exercises available on the CSES platform.

3. Submit a solution:

   ```bash
   python moocfi_cses.py submit <exercise_id> <path_to_solution_file>
   ```

   Replace `<exercise_id>` with the ID of the exercise you want to submit a solution for, and `<path_to_solution_file>` with the path to your solution file.

## Contributing

Contributions are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
