import argparse
import importlib.metadata
import json
import logging
import sys
from dataclasses import dataclass
from enum import Enum
from getpass import getpass
from pathlib import Path
from time import sleep
from typing import AnyStr, Optional
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, tostring

import html5lib
import platformdirs
from html2text import html2text

from .session import MoocfiCsesSession as Session

logger = logging.getLogger(name="tyora")
try:
    __version__ = importlib.metadata.version("tyora")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

PROG_NAME = "tyora"
CONF_FILE = platformdirs.user_config_path(PROG_NAME) / "config.json"
STATE_DIR = platformdirs.user_state_path(f"{PROG_NAME}")


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
    file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    print("Writing config to file")
    with open(file_path, "w") as f:
        json.dump(config, f)


def read_config(configfile: str) -> dict[str, str]:
    config = dict()
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
            return json.load(f)
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


def find_link(html: AnyStr, xpath: str) -> dict[str, Optional[str]]:
    """Search for html link by xpath and return dict with href and text"""
    anchor_element = html5lib.parse(html, namespaceHTMLElements=False).find(xpath)
    link_data = dict()
    if anchor_element is not None:
        link_data["href"] = anchor_element.get("href")
        link_data["text"] = anchor_element.text

    return link_data


def parse_form(html: AnyStr, xpath: str = ".//form") -> dict:
    """Search for the first form in html and return dict with action and all other found inputs"""
    form_element = html5lib.parse(html, namespaceHTMLElements=False).find(xpath)
    form_data = dict()
    if form_element is not None:
        form_data["_action"] = form_element.get("action")
        for form_input in form_element.iter("input"):
            form_key = form_input.get("name") or ""
            form_value = form_input.get("value") or ""
            form_data[form_key] = form_value

    return form_data


class TaskState(Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


TASK_STATE_ICON = {
    TaskState.COMPLETE: "✅",
    TaskState.INCOMPLETE: "❌",
}


@dataclass
class Task:
    id: str
    name: str
    state: TaskState
    description: Optional[str] = None
    code: Optional[str] = None
    submit_file: Optional[str] = None
    submit_link: Optional[str] = None


def parse_task_list(html: AnyStr) -> list[Task]:
    """Parse html to find tasks and their status, return something useful, possibly a specific data class"""
    content_element = html5lib.parse(html, namespaceHTMLElements=False).find(
        './/div[@class="content"]'
    )
    task_list = list()
    if content_element is not None:
        for item in content_element.findall('.//li[@class="task"]'):
            item_id = None
            item_name = None
            item_class = None

            item_link = item.find("a")
            if item_link is not None:
                item_name = item_link.text or ""
                item_id = item_link.get("href", "").split("/")[-1]

            item_spans = item.findall("span") or []
            item_span = next(
                (span for span in item_spans if span.get("class", "") != "detail"), None
            )
            if item_span is not None:
                item_class = item_span.get("class", "")

            if item_id and item_name and item_class:
                task = Task(
                    id=item_id,
                    name=item_name,
                    state=(
                        TaskState.COMPLETE
                        if "full" in item_class
                        else TaskState.INCOMPLETE
                    ),
                )
                task_list.append(task)

    return task_list


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


def parse_task(html: AnyStr) -> Task:
    root = html5lib.parse(html, namespaceHTMLElements=False)
    task_link_element = root.find('.//div[@class="nav sidebar"]/a')
    task_link = task_link_element if task_link_element is not None else Element("a")
    task_id = task_link.get("href", "").split("/")[-1]
    if not task_id:
        raise ValueError("Failed to find task id")
    task_name = task_link.text or None
    if not task_name:
        raise ValueError("Failed to find task name")
    task_span_element = task_link.find("span")
    task_span = task_span_element if task_span_element is not None else Element("span")
    task_span_class = task_span.get("class", "")
    desc_div_element = root.find('.//div[@class="md"]')
    desc_div = desc_div_element if desc_div_element is not None else Element("div")
    description = html2text(tostring(desc_div).decode("utf8"))
    code = root.findtext(".//pre", None)
    submit_link_element = root.find('.//a[.="Submit"]')
    submit_link = (
        submit_link_element.get("href", None)
        if submit_link_element is not None
        else None
    )

    submit_file = next(
        iter(
            [
                code_element.text
                for code_element in root.findall(".//code")
                if code_element.text is not None and ".py" in code_element.text
            ]
        ),
        None,
    )
    task = Task(
        id=task_id,
        name=task_name,
        state=TaskState.COMPLETE if "full" in task_span_class else TaskState.INCOMPLETE,
        description=description.strip(),
        code=code,
        submit_file=submit_file,
        submit_link=submit_link,
    )

    return task


def print_task(task: Task) -> None:
    print(f"{task.id}: {task.name} {TASK_STATE_ICON[task.state]}")
    print(task.description)
    print(f"\nSubmission file name: {task.submit_file}")


# def submit_task(task_id: str, filename: str) -> None:
#     """submit file to the submit form or task_id"""
#     html = session.http_request(urljoin(base_url, f"task/{task_id}"))
#     task = parse_task(html)
#     answer = input("Do you want to submit this task? (y/n): ")
#     if answer in ('y', 'Y'):
#         with open(filename, 'r') as f:


def parse_submit_result(html: AnyStr) -> dict[str, str]:
    root = html5lib.parse(html, namespaceHTMLElements=False)
    submit_status_element = root.find('.//td[.="Status:"]/..') or Element("td")
    submit_status_span_element = submit_status_element.find("td/span") or Element(
        "span"
    )
    submit_status = submit_status_span_element.text or ""
    submit_result_element = root.find('.//td[.="Result:"]/..') or Element("td")
    submit_result_span_element = submit_result_element.find("td/span") or Element(
        "span"
    )
    submit_result = submit_result_span_element.text or ""

    return {
        "status": submit_status.lower(),
        "result": submit_result.lower(),
    }


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
    cookies = dict()
    if not args.no_state:
        if not STATE_DIR.exists():
            STATE_DIR.mkdir(parents=True, exist_ok=True)
        cookiefile = STATE_DIR / "cookies.txt"
        cookies = read_cookie_file(str(cookiefile))

    session = Session(
        username=config["username"],
        password=config["password"],
        base_url=base_url,
        cookies=cookies,
    )
    session.login()

    if not args.no_state and cookiefile:
        cookies = session.cookies.get_dict()
        write_cookie_file(str(cookiefile), cookies)

    if args.cmd == "list":
        res = session.get(urljoin(base_url, "list"))
        res.raise_for_status()
        task_list = parse_task_list(res.text)
        print_task_list(task_list, filter=args.filter, limit=args.limit)

    if args.cmd == "show":
        res = session.get(urljoin(base_url, f"task/{args.task_id}"))
        res.raise_for_status()
        try:
            task = parse_task(res.text)
        except ValueError as e:
            logger.debug(f"Error parsing task: {e}")
            raise
        print_task(task)

    if args.cmd == "submit":
        res = session.get(urljoin(base_url, f"task/{args.task_id}"))
        res.raise_for_status()
        task = parse_task(res.text)
        if not task.submit_file and not args.filename:
            raise ValueError("No submission filename found")
        if not task.submit_link:
            raise ValueError("No submission link found")
        submit_file = args.filename or task.submit_file or ""

        res = session.get(urljoin(base_url, task.submit_link))
        res.raise_for_status()
        submit_form_data = parse_form(res.text)
        action = submit_form_data.pop("_action")

        for key, value in submit_form_data.items():
            submit_form_data[key] = (None, value)
        submit_form_data["file"] = (submit_file, open(submit_file, "rb"))
        submit_form_data["lang"] = (None, "Python3")
        submit_form_data["option"] = (None, "CPython3")

        res = session.post(urljoin(base_url, action), files=submit_form_data)
        res.raise_for_status()
        html = res.text
        result_url = res.url
        print("Waiting for test results.", end="")
        while "Test report" not in html:
            print(".", end="")
            sleep(1)
            res = session.get(result_url)
            res.raise_for_status()

        print()
        results = parse_submit_result(res.text)

        print(f"Submission status: {results['status']}")
        print(f"Submission result: {results['result']}")


if __name__ == "__main__":
    main()
