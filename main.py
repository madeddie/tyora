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
import urllib.request

import htmlement

base_url = "https://cses.fi/dsa24k/list/"


class LinkFinderParser(HTMLParser):
    def __init__(self, attrib: tuple[str, str | None]) -> None:
        HTMLParser.__init__(self)
        self.attrib = attrib
        self.record = False
        self.link = str()
        self.data = list()

    def feed(self, data: str) -> None:
        data = data.decode("utf8") if isinstance(data, bytes) else data
        return super().feed(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        href = ""
        is_valid = False
        if tag == "a":
            for attr in attrs:
                if attr == self.attrib:
                    is_valid = True
                    self.record = True
                elif attr[0] == "href":
                    href = attr[1]

            if is_valid:
                self.link = href

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.record:
            self.record = False

    def handle_data(self, data: str) -> None:
        if self.record:
            self.data.append(data)


class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.action = str()
        self.form = dict()
        self.record = False

    def feed(self, data: str) -> None:
        data = data.decode("utf8") if isinstance(data, bytes) else data
        return super().feed(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "form":
            self.record = True
            for attr in attrs:
                if attr[0] == "action":
                    self.action = attr[1]
        elif tag == "input" and self.record:
            name = ""
            value = ""
            for attr in attrs:
                if attr[0] == "name":
                    name = attr[1]
                elif attr[0] == "value":
                    value = attr[1]
            if name:
                self.form[name] = value

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self.record:
            self.record = False


class MoocCsesSession:
    def __init__(self, configfile: str | None = None) -> None:
        self._configfile = configfile if configfile else "config.json"
        self._config = self._read_config(self._configfile)
        self._cj = http.cookiejar.LWPCookieJar(self._config["cookies_file"])
        self._session = self._get_session()

    @staticmethod
    def parse_to_etree(fileobj):
        return htmlement.parse(fileobj)

    def _get_session(self) -> urllib.request.OpenerDirector:
        try:
            self._cj.load(ignore_discard=True)
        except FileNotFoundError:
            pass

        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cj))

    @property
    def _is_logged_in(self) -> bool:
        res = self._session.open(base_url)
        root = self.parse_to_etree(res)
        # parser = LinkFinderParser(("class", "account"))
        # parser.feed(res.read())

        #return self._config["username"] in next(iter(parser.data), "")
        return self._config["username"] in root.find('.//a[@class="account"]').text

    def _login(self, login: str = "", passwd: str = "") -> bool:
        username = login if login else self._config["username"]
        password = passwd if passwd else self._config["password"]
        res = self.retrieve(base_url, skip_login=True)
        # parser = LinkFinderParser(("class", "account"))
        # parser.feed(res.read())
        # login_url = urllib.parse.urljoin(res.url, parser.link)
        root = self.parse_to_etree(res)
        login_url = urllib.parse.urljoin(res.url, root.find('.//a[@class="account"]').get('href'))

        res = self.retrieve(login_url, referer=res.url, skip_login=True)
        # parser = FormParser()
        # parser.feed(res.read())
        # form_data = parser.form
        root = htmlement.parse(res)
        action = root.find('.//form').get('action')
        form_data = dict()
        for form_input in root.find('.//form').iter('input'):
            form_data[form_input.get('name')] = form_input.get('value', '')

        form_data["session[login]"] = username
        form_data["session[password]"] = password
        # post_data = urllib.parse.urlencode(form_data).encode("ascii")

        res = self.retrieve(
            urllib.parse.urljoin(res.url, action),
            referer=res.url,
            data=urllib.parse.urlencode(form_data).encode("ascii"),
            skip_login=True,
        )

        return self._is_logged_in

    def _read_config(self, configfile: str):
        try:
            with open(configfile, "r") as f:
                config = json.load(f)
                for setting in ("username", "password", "cookies_file"):
                    assert setting in config
        except (FileNotFoundError, json.JSONDecodeError):
            print("Invalid config, generating new one")
            username = self._ask_input("Your tmc.mooc.fi username: ", True)
            password = self._ask_input("Your tmc.mooc.fi password: ", True, True)
            cookies_file = (
                input("Name of cookies file [cookies.txt]: ") or "cookies.txt"
            )
            config = {
                "username": username,
                "password": password,
                "cookies_file": cookies_file,
            }
            self._write_config(configfile, config)

        return config

    @staticmethod
    def _ask_input(prompt: str, required: bool = False, masked: bool = False) -> str:
        if not required:
            return input(prompt)

        output = ""
        while not output:
            if masked:
                output = getpass(prompt)
            else:
                output = input(prompt)
        return output

    def _write_config(self, configfile: str, config: dict) -> None:
        with open(configfile, "w+") as f:
            json.dump(config, f)

    def retrieve(
        self,
        url: str,
        referer: str = "",
        data: bytes | None = None,
        skip_login: bool = False,
    ):
        if not skip_login and not self._is_logged_in:
            if not self._login():
                raise RuntimeError("Failed to login")

        if referer:
            self._session.addheaders = [("referer", referer)]
        res = self._session.open(url, data)
        self._cj.save(ignore_discard=True)

        return res


def main():
    # config_file = "moocfi_cses.json"
    moocsess = MoocCsesSession()
    res = moocsess.retrieve(base_url)

    # soup = BeautifulSoup(res.text, 'html.parser')
    # print(soup.find('a', class_='account').string)
    #
    # for item in soup.find_all('li', class_='task'):
    #     completed = '✅' if 'full' in item.find('span', class_='task-score')['class'] else '❌'
    #     print(completed, item.a.get('href'), item.a.string)
    root = moocsess.parse_to_etree(res)
    #return res
    content = root.find('.//div[@class="content"]')
    #title = 

if __name__ == "__main__":
    main()
