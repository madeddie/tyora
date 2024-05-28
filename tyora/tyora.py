import argparse
import importlib.metadata
import json
import logging
import sys
from getpass import getpass
from pathlib import Path
from time import sleep
from typing import Optional, no_type_check

import platformdirs

from .client import Client, Task, TaskState, parse_submit_result
from .session import MoocfiCsesSession as Session

logger = logging.getLogger(name="tyora")
try:
    __version__ = importlib.metadata.version("tyora")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

PROG_NAME = "tyora"
CONF_FILE = platformdirs.user_config_path(PROG_NAME) / "config.json"
STATE_DIR = platformdirs.user_state_path(f"{PROG_NAME}")


# Disable typechecking for the argparse function calls since we ignore most returned values
@no_type_check
def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interact with mooc.fi CSES instance")
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("-u", "--username", help="tmc.mooc.fi username")
    parser.add_argument("-p", "--password", help="tmc.mooc.fi password")
    parser.add_argument(
        "--debug", help="set logging level to debug", action="store_true"
    )
    parser.add_argument(
        "--course",
        help="SLUG of the course (default: %(default)s)",
        default="dsa24k",
    )
    parser.add_argument(
        "--config",
        help="Location of config file (default: %(default)s)",
        default=CONF_FILE,
    )
    parser.add_argument(
        "--no-state",
        help="Don't store cookies or cache (they're used for faster access on the future runs)",
        action="store_true",
    )
    subparsers = parser.add_subparsers(required=True, title="commands", dest="cmd")

    # login subparser
    subparsers.add_parser("login", help="Login to mooc.fi CSES")

    # list exercises subparser
    parser_list = subparsers.add_parser("list", help="List exercises")
    parser_list.add_argument(
        "--filter",
        help="List only complete or incomplete tasks (default: all)",
        choices=["complete", "incomplete"],
    )
    parser_list.add_argument(
        "--limit", help="Maximum amount of items to list", type=int
    )

    # show exercise subparser
    parser_show = subparsers.add_parser("show", help="Show details of an exercise")
    parser_show.add_argument("task_id", help="Numerical task identifier")

    # submit exercise solution subparser
    parser_submit = subparsers.add_parser("submit", help="Submit an exercise solution")
    parser_submit.add_argument(
        "--filename",
        help="Filename of the solution to submit (if not given will be guessed from task description)",
    )
    parser_submit.add_argument("task_id", help="Numerical task identifier")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args(args)


def create_config() -> dict[str, str]:
    username = input("Your tmc.mooc.fi username: ")
    password = getpass("Your tmc.mooc.fi password: ")
    config = {
        "username": username,
        "password": password,
    }

    return config


def write_config(configfile: str, config: dict[str, str]) -> None:
    file_path = Path(configfile).expanduser()
    if file_path.exists():
        # TODO: https://github.com/madeddie/tyora/issues/28
        ...
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    print("Writing config to file")
    with open(file_path, "w") as f:
        json.dump(config, f)


def read_config(configfile: str) -> dict[str, str]:
    config: dict[str, str] = dict()
    file_path = Path(configfile).expanduser()
    with open(file_path, "r") as f:
        config = json.load(f)
        for setting in ("username", "password"):
            assert setting in config
    return config


def read_cookie_file(cookiefile: str) -> dict[str, str]:
    """
    Reads cookies from a JSON formatted file.

    Args:
        cookiefile: str path to the file containing cookies.

    Returns:
        A dictionary of cookies.
    """
    try:
        with open(cookiefile, "r") as f:
            cookies: dict[str, str] = json.load(f)
            return cookies
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.debug(f"Error reading cookies from {cookiefile}: {e}")
    return {}


def write_cookie_file(cookiefile: str, cookies: dict[str, str]) -> None:
    """
    Writes cookies to a file in JSON format.

    Args:
        cookiefile: Path to the file for storing cookies.
        cookies: A dictionary of cookies to write.
    """
    with open(cookiefile, "w") as f:
        json.dump(cookies, f)


TASK_STATE_ICON = {
    TaskState.COMPLETE: "✅",
    TaskState.INCOMPLETE: "❌",
}


def print_task_list(
    task_list: list[Task], filter: Optional[str] = None, limit: Optional[int] = None
) -> None:
    count: int = 0
    for task in task_list:
        if not filter or filter == task.state.value:
            print(f"- {task.id}: {task.name} {TASK_STATE_ICON[task.state]}")
            count += 1
            if limit and count >= limit:
                return


def print_task(task: Task) -> None:
    print(f"{task.id}: {task.name} {TASK_STATE_ICON[task.state]}")
    print(task.description)
    print(f"\nSubmission file name: {task.submit_file}")


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.cmd == "login":
        config = create_config()
        write_config(args.config, config)
        return

    config = read_config(args.config)

    # Merge cli args and configfile parameters in one dict
    config.update((k, v) for k, v in vars(args).items() if v is not None)

    base_url = f"https://cses.fi/{config['course']}/"

    cookiefile = None
    cookies: dict[str, str] = dict()
    if not args.no_state:
        if not STATE_DIR.exists():
            STATE_DIR.mkdir(parents=True, exist_ok=True)
        cookiefile = STATE_DIR / "cookies.json"
        cookies = read_cookie_file(str(cookiefile))

    session = Session(
        base_url=base_url,
        cookies=cookies,
    )
    # TODO: make logging in optional for list and show commands
    session.login(username=config["username"], password=config["password"])
    client = Client(session)

    if not args.no_state and cookiefile:
        cookies = session.cookies.get_dict()
        write_cookie_file(str(cookiefile), cookies)

    if args.cmd == "list":
        print_task_list(client.get_task_list(), filter=args.filter, limit=args.limit)

    if args.cmd == "show":
        print_task(client.get_task(args.task_id))

    if args.cmd == "submit":
        # TODO allow user to paste the code in or even pipe it in
        with open(args.filename) as f:
            submission_code = f.read()

        result_url = client.submit_task(
            task_id=args.task_id,
            filename=args.filename,
            submission=submission_code,
        )
        print("Waiting for test results.", end="")
        while True:
            print(".", end="")
            res = session.get(result_url)
            print(res.text)
            res.raise_for_status()
            if "Test report" in res.text:
                break
            sleep(1)

        print()
        results = parse_submit_result(res.text)

        print(f"Submission status: {results['status']}")
        print(f"Submission result: {results['result']}")


if __name__ == "__main__":
    main()
