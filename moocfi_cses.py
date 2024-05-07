# TEST: see if we can work with cookies as dict instead of cookiejar
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
import json
import urllib.parse
import http.cookiejar
from pathlib import Path
from typing import AnyStr

import htmlement
import requests
from requests.models import Response


@dataclass
class Session:
    username: str
    password: str
    base_url: str
    cookiejar: http.cookiejar.CookieJar = field(
        default_factory=http.cookiejar.CookieJar
    )

    def __post_init__(self):
        self.http_session = requests.Session()

    @property
    def is_logged_in(self) -> bool:
        html = self.http_request(self.base_url).text
        login_link = find_link(html, './/a[@class="account"]')
        return self.username in login_link.get("text", "")

    # TODO: add a debug flag/verbose flag and allow printing of html and forms
    def login(self) -> None:
        if self.is_logged_in:
            return

        res = self.http_request(self.base_url)
        login_link = find_link(res.text, './/a[@class="account"]')
        if login_link:
            login_url = urllib.parse.urljoin(res.url, login_link.get("href"))
        else:
            raise ValueError("Failed to find login url")

        res = self.http_request(login_url, referer=res.url)
        login_form = parse_form(res.text, ".//form")
        if login_form:
            action = login_form.get("_action")
            login_form.pop("_action")
        else:
            raise ValueError("Failed to find login form")

        login_form["session[login]"] = self.username
        login_form["session[password]"] = self.password

        self.http_request(
            url=urllib.parse.urljoin(res.url, action), referer=res.url, data=login_form
        )
        if not self.is_logged_in:
            raise ValueError("Login failed")

    def http_request(
        self,
        url: str,
        referer: str = "",
        data: dict | None = None,
    ) -> Response:
        if referer:
            self.http_session.headers.update({"referer": referer})
        if data:
            res = self.http_session.post(url, data)
        else:
            res = self.http_session.get(url)

        return res


# TODO: replace with click
def parse_args(args: list | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interact with mooc.fi CSES instance")
    parser.add_argument("--username", help="tmc.mooc.fi username")
    parser.add_argument("--password", help="tmc.mooc.fi password")
    parser.add_argument(
        "--course", help="SLUG of the course (default: %(default)s)", default="dsa24k"
    ),  # pyright: ignore[reportUnusedExpression]
    parser.add_argument(
        "--config",
        help="Location of config file (default: %(default)s)",
        default="~/.config/moocfi_cses/config.json",
    ),  # pyright: ignore[reportUnusedExpression]
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
def write_config(config_file: str, config: dict) -> None:
    print("Writing config to file")
    with open(config_file, "w") as f:
        json.dump(config, f)


# TODO: check if path exists
# TODO: try/except around open and json.load, return empty dict on failure
def read_config(configfile: str) -> dict:
    config = dict()
    file = Path(configfile).expanduser()
    with open(file, "r") as f:
        config = json.load(f)
        for setting in ("username", "password"):
            assert setting in config
    return config


# TODO: convert to using a dict
def get_cookiejar(cookiefile: str) -> http.cookiejar.LWPCookieJar:
    cookiejar = http.cookiejar.LWPCookieJar(cookiefile)
    try:
        cookiejar.load(ignore_discard=True)
    except FileNotFoundError:
        # TODO: handle exception?
        pass

    return cookiejar


def find_link(html: AnyStr, xpath: str) -> dict[str, str]:
    """Search for html link by xpath and return dict with href and text"""
    anchor_element = htmlement.fromstring(html).find(xpath)
    link_data = dict()
    if anchor_element is not None:
        link_data["href"] = anchor_element.get("href")
        link_data["text"] = anchor_element.text

    return link_data


def parse_form(html: AnyStr, xpath: str = ".//form") -> dict[str, str]:
    """Search for the first form in html and return dict with action and all other found inputs"""
    form_element = htmlement.fromstring(html).find(xpath)
    form_data = dict()
    if form_element is not None:
        form_data["_action"] = form_element.get("action")
        for form_input in form_element.iter("input"):
            form_data[form_input.get("name")] = form_input.get("value", "")

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
            id = name = span_class = ""
            link_item = item.find("a")
            if link_item is not None:
                name = link_item.text or ""
                id = link_item.get("href", "").split("/")[-1]
            span_item = item.find('span[@class!="detail"]')
            if span_item is not None:
                span_class = span_item.get("class", "")
                "i❌  ✅ X or ✔"
            if id and name and span_class:
                task = Task(
                    id=id,
                    name=name,
                    complete="full" in span_class,
                )
                task_list.append(task)

    return task_list


# TODO: todo todo todo
def submit_task(task_id: str, filename: str) -> None:
    """submit file to the submit form or task_id"""
    # NOTE: use parse_form and submit_form
    ...


# TODO: todo todo todo
def parse_task(html: str | bytes, task: Task) -> Task:
    task = Task("a", "b", True)
    return task


# TODO: todo todo
def list_tasks(html: str | bytes) -> None:
    print("These are you tasks")
    print("these are the args")
    print(html)


# TODO: how to make this more functional?
def submit_form(session: requests.sessions.Session, url: str, data: dict) -> None:
    form_data = urllib.parse.urlencode(data).encode("ascii")
    session.post(url, data=form_data)


def main() -> None:
    # TODO: make state configurable, so people can choose not to store state
    state_dir = "~/.local/state/moocfi_cses"

    args = parse_args()

    if args.cmd == "configure":
        config = create_config()
        write_config(args.config, config)
        return

    config = read_config(args.config)

    # Merge args and config options in 1 dict
    config.update((k, v) for k, v in vars(args).items() if v is not None)
    print(config)
    base_url = f"https://cses.fi/{config['course']}/list/"
    cookiejar = get_cookiejar(str(Path(state_dir + "/cookies.txt").expanduser()))

    session = Session(
        username=config["username"],
        password=config["password"],
        base_url=base_url,
        cookiejar=cookiejar,
    )
    session.login()
    cookiejar.save(ignore_discard=True)

    if args.cmd == "list":
        res = session.http_request(base_url)
        task_list = parse_task_list(res.text)
        print(task_list[0])


if __name__ == "__main__":
    main()
