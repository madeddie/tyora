# TEST: is the `click` library a useful option?
# TODO: if config doesn't exist fail and ask to run config creation
# TODO: make sure the correct directories exist
# TODO: check validity of config after creation (can we log in?)
# TODO: add exercise list parse, list of exercises, name, status, possible: week and deadline
# TODO: UI for checking exercise description
# TODO: UI for submitting solutions
import argparse
from dataclasses import dataclass, field
from getpass import getpass
import logging
import json
import urllib.parse
from pathlib import Path
from typing import AnyStr, Optional

import htmlement
import requests


logger = logging.getLogger(name="moocfi_cses")


@dataclass
class Session:
    username: str
    password: str
    base_url: str
    cookies: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.http_session = requests.Session()
        self.http_session.cookies = requests.utils.cookiejar_from_dict(self.cookies)  # type: ignore[no-untyped-call]

    @property
    def is_logged_in(self) -> bool:
        html = self.http_request(self.base_url)
        login_link = find_link(html, './/a[@class="account"]')
        login_text = login_link.get("text") or ""
        return self.username in login_text

    # TODO: add a debug flag/verbose flag and allow printing of html and forms
    def login(self) -> None:
        """Logs into the site using webscraping

        Steps:
        - checks if already logged in
        - retrieves base URL
        - finds and retrieves login URL
        - finds and submits login form
        - checks if logged in
        """
        if self.is_logged_in:
            return

        res = self.http_session.get(self.base_url)
        login_link = find_link(res.text, './/a[@class="account"]')
        if login_link:
            login_url = urllib.parse.urljoin(res.url, login_link.get("href"))
        else:
            logging.debug(
                f"url: {res.url}, status: {res.status_code}\nhtml:\n{res.text}"
            )
            raise ValueError("Failed to find login url")

        res = self.http_session.get(login_url, headers={"referer": res.url})
        login_form = parse_form(res.text, ".//form")
        if login_form:
            action = login_form.get("_action")
            login_form.pop("_action")
        else:
            logging.debug(
                f"url: {res.url}, status: {res.status_code}\nhtml:\n{res.text}"
            )
            raise ValueError("Failed to find login form")

        login_form["session[login]"] = self.username
        login_form["session[password]"] = self.password

        self.http_session.post(
            url=urllib.parse.urljoin(res.url, action),
            headers={"referer": res.url},
            data=login_form,
        )

        if not self.is_logged_in:
            logging.debug(
                f"url: {res.url}, status: {res.status_code}\nhtml:\n{res.text}"
            )
            raise ValueError("Login failed")

    def http_request(
        self,
        url: str,
        referer: str = "",
        data: Optional[dict[str, str]] = None,
    ) -> str:
        if referer:
            self.http_session.headers.update({"referer": referer})
        if data:
            res = self.http_session.post(url, data)
        else:
            res = self.http_session.get(url)

        return res.text


# TODO: replace with click
def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interact with mooc.fi CSES instance")
    parser.add_argument("--username", help="tmc.mooc.fi username")
    parser.add_argument("--password", help="tmc.mooc.fi password")
    (
        parser.add_argument(
            "--course",
            help="SLUG of the course (default: %(default)s)",
            default="dsa24k",
        ),
    )  # pyright: ignore[reportUnusedExpression]
    (
        parser.add_argument(
            "--config",
            help="Location of config file (default: %(default)s)",
            default="~/.config/moocfi_cses/config.json",
        ),
    )  # pyright: ignore[reportUnusedExpression]
    parser.add_argument(
        "--no-state",
        action="store_true",
        help="Don't store cookies or cache (used for faster access on the future runs)",
    )
    subparsers = parser.add_subparsers(required=True)

    parser_config = subparsers.add_parser("configure", help="configure moocfi_cses")
    parser_config.set_defaults(cmd="configure")

    parser_list = subparsers.add_parser("list", help="list exercises")
    parser_list.set_defaults(cmd="list")

    return parser.parse_args(args)


def create_config() -> dict[str, str]:
    # TODO: try to read an existing config file and give the values as default values
    username = input("Your tmc.mooc.fi username: ")
    password = getpass("Your tmc.mooc.fi password: ")
    config = {
        "username": username,
        "password": password,
    }

    return config


# TODO: check if file exists and ask permission to overwrite
# TODO: check if path exists, otherwise create
def write_config(config_file: str, config: dict[str, str]) -> None:
    print("Writing config to file")
    with open(config_file, "w") as f:
        json.dump(config, f)


# TODO: check if path exists
# TODO: try/except around open and json.load, return empty dict on failure
def read_config(configfile: str) -> dict[str, str]:
    config = dict()
    file = Path(configfile).expanduser()
    with open(file, "r") as f:
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
        logging.debug(f"Error reading cookies from {cookiefile}: {e}")
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


def find_link(html: AnyStr, xpath: str) -> dict[str, str | None]:
    """Search for html link by xpath and return dict with href and text"""
    anchor_element = htmlement.fromstring(html).find(xpath)
    link_data = dict()
    if anchor_element is not None:
        link_data["href"] = anchor_element.get("href")
        link_data["text"] = anchor_element.text

    return link_data


def parse_form(html: AnyStr, xpath: str = ".//form") -> dict[str, str | None]:
    """Search for the first form in html and return dict with action and all other found inputs"""
    form_element = htmlement.fromstring(html).find(xpath)
    form_data = dict()
    if form_element is not None:
        form_data["_action"] = form_element.get("action")
        for form_input in form_element.iter("input"):
            form_key = form_input.get("name") or ""
            form_value = form_input.get("value") or ""
            form_data[form_key] = form_value

    return form_data


@dataclass
class Task:
    id: str
    name: str
    complete: bool


# NOTE: I could simply use html2text to output the list of tasks
# it needs some work to replace the <span task-score icon full with an actual icon
# and do we want people to choose the task by name or by ID (or both?)
def parse_task_list(html: str | bytes) -> list[Task]:
    """Parse html to find tasks and their status, return something useful, possibly a specific data class"""
    content_element = htmlement.fromstring(html).find('.//div[@class="content"]')
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

            item_span = item.find('span[@class!="detail"]')
            if item_span is not None:
                item_class = item_span.get("class", "")

            if item_id and item_name and item_class:
                task = Task(
                    id=item_id,
                    name=item_name,
                    complete="full" in item_class,
                )
                task_list.append(task)

    return task_list


TASK_DONE_ICON = {True: "✅", False: "❌"}


# TODO: todo todo
def print_task_list(html: str | bytes) -> None:
    "i❌  ✅ X or ✔"
    print("These are you tasks")
    print("these are the args")
    print(html)


# TODO: todo todo todo
def submit_task(task_id: str, filename: str) -> None:
    """submit file to the submit form or task_id"""
    # NOTE: use parse_form
    ...


# TODO: todo todo todo
def parse_task(html: str | bytes, task: Task) -> Task:
    task = Task("a", "b", True)
    return task


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.cmd == "configure":
        config = create_config()
        write_config(args.config, config)
        return

    config = read_config(args.config)

    # Merge cli args and configfile parameters in one dict
    config.update((k, v) for k, v in vars(args).items() if v is not None)

    base_url = f"https://cses.fi/{config['course']}/list/"

    cookiefile = None
    cookies = dict()
    print(args)
    if not args.no_state:
        state_dir = Path("~/.local/state/moocfi_cses").expanduser()
        if not state_dir.exists():
            state_dir.mkdir(parents=True)
        cookiefile = state_dir / "cookies.txt"
        cookies = read_cookie_file(str(cookiefile))

    session = Session(
        username=config["username"],
        password=config["password"],
        base_url=base_url,
        cookies=cookies,
    )
    session.login()

    if not args.no_state and cookiefile:
        cookies = requests.utils.dict_from_cookiejar(session.http_session.cookies)
        write_cookie_file(str(cookiefile), cookies)

    if args.cmd == "list":
        html = session.http_request(base_url)
        task_list = parse_task_list(html)
        for task in task_list:
            print(f"- {task.id}: {task.name} {TASK_DONE_ICON[task.complete]}")


if __name__ == "__main__":
    main()
