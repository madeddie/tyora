# TODO: if config doesn't exist fail and ask to run config creation
# TODO: make sure the correct directories exist
# TODO: use system specific config and state folders for config files and cookies, like ~/.config and ~/.local/state
# TODO: check validity of config after creation (can we log in?)
# TODO: add exercise list parse, list of exercises, name, status, possible: week and deadline
# TODO: UI to config username and password
# TODO: UI for checking exercise description
# TODO: UI for submitting solutions
from html.parser import HTMLParser
from getpass import getpass
import json
import urllib.parse
import http.cookiejar
import http.client
import urllib.request
from pathlib import Path

import htmlement

def read_config(config_file: Path) -> dict:
    with open(config_file, "r") as f:
        config = json.load(f)
        for setting in ("username", "password"):
            assert setting in config
    return config

# TODO: not quite functional, move input/getpass to main when implmenting argparse
def write_config(config_file: Path, username: str, password: str) -> None:
    username = input("Your tmc.mooc.fi username: ")
    password = getpass("Your tmc.mooc.fi password: ")
    config = {
        "username": username,
        "password": password,
    }
    print("Writing config to file")
    with open(config_file, "w") as f:
       json.dump(config, f)

def create_session(cookiejar: http.cookiejar.CookieJar) -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))

def open_url(url: str, session: urllib.request.OpenerDirector, referer: str = "", data: bytes | None = None) -> http.client.HTTPResponse:
    if referer:
        session.addheaders = [("referer", referer)]
    res = session.open(url, data)

    return res

def login(session: urllib.request.OpenerDirector, username: str, password: str, base_url: str) -> urllib.request.OpenerDirector | bool:
    res = session.open(base_url)
    login_element = htmlement.parse(res).find('.//a[@class="account"]')
    if login_element is not None:
        login_url = urllib.parse.urljoin(res.url, login_element.get('href'))
    else:
        # raise ValueError("Failed to find login_url")
        return False

    session.addheaders = [("referer", res.url)]
    res = session.open(login_url)
    root = htmlement.parse(res)
    action_element = root.find('.//form')
    if action_element is not None:
        action = action_element.get('action')
    else:
        # raise ValueError("Failed to find action parameter of login form")
        return False
    form_element = root.find('.//form')
    if form_element is not None:
        form_data = dict()
        for form_input in form_element.iter('input'):
            form_data[form_input.get('name')] = form_input.get('value', '')
    else:
        # raise ValueError("Failed to find form")
        return False

    form_data["session[login]"] = username
    form_data["session[password]"] = password
    form_data = urllib.parse.urlencode(form_data).encode("ascii")

    session.addheaders = [("referer", res.url)]
    res = session.open(urllib.parse.urljoin(res.url, action), data=form_data)
    
    return session

def main():
    # TODO: make base_url configurable based on course
    base_url = "https://cses.fi/dsa24k/list/"
    config_file = Path.home() / '.config' / 'moocfi_cses' / 'config.json'
    state_dir = Path.home() / '.local' / 'state' / 'moocfi_cses'

    config = read_config(config_file)
    cookiejar = http.cookiejar.LWPCookieJar(state_dir / 'cookies.txt')
    try:
        cookiejar.load(ignore_discard=True)
    except FileNotFoundError:
        # TODO: handle exception?
        pass

    session = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))
    res = open_url(base_url, session)
    root = htmlement.parse(res)
    login_element = root.find('.//a[@class="account"]')
    if login_element is not None:
        login_text = login_element.text
    else:
        login_text = ''
    if not config["username"] in login_text:
        print('trying to log in')
        login(session, config['username'], config['password'], base_url)
    cookiejar.save(ignore_discard=True)

    res = open_url(base_url, session)
    # print(res.read())
    # print(type(res))

if __name__ == "__main__":
    main()