# NOTE: maybe it'd be good to have at least a Session object with the http_request and login methods
# TODO: if config doesn't exist fail and ask to run config creation
# TODO: make sure the correct directories exist
# TODO: check validity of config after creation (can we log in?)
# TODO: add exercise list parse, list of exercises, name, status, possible: week and deadline
# TODO: UI for checking exercise description
# TODO: UI for submitting solutions
import argparse
from getpass import getpass
import json
import urllib.parse
import http.cookiejar
import http.client
import urllib.request
from pathlib import Path

import htmlement


class Session():
    def __init__(self, username: str, password: str, base_url: str, cookiejar: http.cookiejar.CookieJar | None = None) -> None:
        self.username = username
        self.password = password
        self.base_url = base_url
        self.cookiejar = cookiejar if cookiejar else http.cookiejar.CookieJar()
        self.session = self.get_session()

    def get_session(self) -> urllib.request.OpenerDirector:
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))

    @property
    def is_logged_in(self) -> bool:
        res = self.session.open(self.base_url)
        login_link = find_link(res.read(), './/a[@class="account"]')
        if self.username in login_link.get("text", ""):
            return True

        return False

    # TODO: add a debug flag/verbose flag and allow printing of html and forms
    # TODO: see if we can suffice with passing the referer header to the open/http_request method instead of to the session
    def login(self) -> None:
        if self.is_logged_in:
            return

        res = self.session.open(self.base_url)
        login_link = find_link(res.read(), './/a[@class="account"]')
        if login_link:
            login_url = urllib.parse.urljoin(res.url, login_link.get("href"))
        else:
            raise ValueError("Failed to find login_url")

        self.session.addheaders = [("referer", res.url)]
        res = self.session.open(login_url)
        login_form = parse_form(res.read(), ".//form")
        if login_form:
            action = login_form.get("_action")
            login_form.pop("_action")
        else:
            raise ValueError("Failed to find form")

        login_form["session[login]"] = self.username
        login_form["session[password]"] = self.password

        self.session.addheaders = [("referer", res.url)]
        submit_form(self.session, urllib.parse.urljoin(res.url, action), login_form)

    def http_request(
        self,
        url: str,
        referer: str = "",
        data: bytes | None = None,
    ) -> http.client.HTTPResponse:
        if referer:
            self.session.addheaders = [("referer", referer)]
        res = self.session.open(url, data)

        return res



def parse_args(args: list | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interact with mooc.fi CSES instance")
    parser.add_argument("--username", help="tmc.mooc.fi username")
    parser.add_argument("--password", help="tmc.mooc.fi password")
    parser.add_argument(
        "--config",
        help="Location of config file (default: %(default)s)",
        default="~/.config/moocfi_cses/config.json",
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


def write_config(config_file: str, config: dict) -> None:
    print("Writing config to file")
    with open(config_file, "w") as f:
        json.dump(config, f)


def read_config(configfile: str) -> dict:
    file = Path(configfile).expanduser()
    with open(file, "r") as f:
        config = json.load(f)
        for setting in ("username", "password"):
            assert setting in config
    return config


# TODO: todo todo
def list_tasks(html: str | bytes) -> None:
    print("These are you tasks")
    print("these are the args")
    print(html)


def get_cookiejar(cookiefile: str) -> http.cookiejar.LWPCookieJar:
    cookiefile = str(Path("cookiefile").expanduser())
    cookiejar = http.cookiejar.LWPCookieJar(cookiefile)
    try:
        cookiejar.load(ignore_discard=True)
    except FileNotFoundError:
        # TODO: handle exception?
        pass

    return cookiejar


# NOTE: maybe split this up in multiple functions, this way they become easier to test by simply inject HTML
# - find_login_url (also useable as input for logged_in() -> bool checker
# - find_login_form or parse_form in login page
# - submit_login_form
def find_link(html: str, xpath: str) -> dict[str, str]:
    """Search for html link by xpath and return dict with href and text"""
    anchor_element = htmlement.fromstring(html).find(xpath)
    link_data = dict()
    if anchor_element is not None:
        link_data["href"] = anchor_element.get("href")
        link_data["text"] = anchor_element.text

    return link_data


def parse_form(html: str, xpath: str = ".//form") -> dict[str, str]:
    """Search for the first form in html and return dict with action and all other found inputs"""
    form_element = htmlement.fromstring(html).find(xpath)
    form_data = dict()
    if form_element is not None:
        form_data["_action"] = form_element.get("action")
        for form_input in form_element.iter("input"):
            form_data[form_input.get("name")] = form_input.get("value", "")

    return form_data

def parse_tasks(html: str):
    '''Parse html to find tasks and their status, return something useful, possibly a specific data class'''
    ...


# TODO: how to make this more functional?
def submit_form(session: urllib.request.OpenerDirector, url: str, data: dict) -> None:
    form_data = urllib.parse.urlencode(data).encode("ascii")
    session.open(url, data=form_data)



def main() -> None:
    # TODO: make base_url configurable based on course
    base_url = "https://cses.fi/dsa24k/list/"
    state_dir = "~/.local/state/moocfi_cses"

    args = parse_args()

    if args.cmd == "configure":
        config = create_config()
        write_config(args.config, config)
        return

    config = read_config(args.config)

    cookiejar = get_cookiejar(str(Path(state_dir + "/cookies.txt").expanduser()))
    session = Session(username=config['username'], password=config['password'], base_url=base_url, cookiejar=cookiejar)
    session.login()
    cookiejar.save(ignore_discard=True)

    if args.cmd == "list":
        res = session.http_request(base_url)
        list_tasks(res.read())


if __name__ == "__main__":
    main()
