from html.parser import HTMLParser
import json
import urllib.parse

import http.cookiejar
import urllib.request

base_url = "https://cses.fi/dsa24k/list/"
config_file = "moocfi_cses.json"
cookies_file = "cookies.txt"


class LinkFinderParser(HTMLParser):
    def __init__(self, attr_key: str, attr_value: str) -> None:
        HTMLParser.__init__(self)
        self.attr_key = attr_key
        self.attr_value = attr_value
        self.record = False
        self.data = list()
        self.link = str()

    def feed(self, data: str) -> None:
        data = data.decode("utf8") if isinstance(data, bytes) else data
        return super().feed(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        href = None
        is_valid = False
        if tag == "a":
            for attr in attrs:
                if attr[0] == self.attr_key and attr[1] == self.attr_value:
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
    def __init__(self, configfile: str) -> None:
        self._configfile = configfile
        self._config = self._read_config(self._configfile)
        self._cj = http.cookiejar.LWPCookieJar(cookies_file)
        self._session = self._get_session()
        # self._logged_in = self._login(self._config['username'], self._config['password'])

    def _get_session(self) -> urllib.request.OpenerDirector:
        try:
            self._cj.load(ignore_discard=True)
        except FileNotFoundError:
            pass

        print(self._cj)
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cj))

    @property
    def _is_logged_in(self) -> bool:
        res = self._session.open(base_url)
        parser = LinkFinderParser("class", "account")
        parser.feed(res.read())

        return self._config["username"] in next(iter(parser.data), "")

    def _login(self, login: str = "", passwd: str = "") -> bool:
        username = login if login else self._config["username"]
        password = passwd if passwd else self._config["password"]
        # res = self._session.open(base_url)
        res = self.retrieve(base_url, skip_login=True)
        print(res.url)
        parser = LinkFinderParser("class", "account")
        parser.feed(res.read())
        login_url = urllib.parse.urljoin(res.url, parser.link)

        # TODO: move referer logic to the rerieve method
        self._session.addheaders = [("referer", res.url)]
        # res = self._session.open(login_url)
        res = self.retrieve(login_url, skip_login=True)
        print(res.url)
        parser = FormParser()
        parser.feed(res.read())
        form_data = parser.form
        form_data["session[login]"] = username
        form_data["session[password]"] = password
        post_data = urllib.parse.urlencode(form_data).encode("ascii")
        print(post_data)

        self._session.addheaders = [("referer", res.url)]
        # res = self._session.open(urllib.parse.urljoin(res.url, parser.action), post_data)
        res = self.retrieve(
            urllib.parse.urljoin(res.url, parser.action), post_data, skip_login=True
        )
        print(res.url)

        return self._is_logged_in

    def _read_config(self, config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
        return config

    # TODO: figure out a better name
    def retrieve(self, url: str, data=None, skip_login=False):
        if not skip_login and not self._is_logged_in:
            if not self._login():
                raise RuntimeError("Failed to login")

        self._session.addheaders = [("referer", url)]
        res = self._session.open(url, data)
        print(self._cj)
        self._cj.save(ignore_discard=True)

        return res


def main():
    import time

    moocsess = MoocCsesSession(config_file)
    start = time.time()
    res = moocsess.retrieve(base_url)
    end = time.time()
    print("Time consumed in working: ", end - start)
    # soup = BeautifulSoup(res.text, 'html.parser')
    # print(soup.find('a', class_='account').string)
    #
    # for item in soup.find_all('li', class_='task'):
    #     completed = '✅' if 'full' in item.find('span', class_='task-score')['class'] else '❌'
    #     print(completed, item.a.get('href'), item.a.string)

    # print(res, res.read())
    start = time.time()
    res = moocsess.retrieve(base_url)
    end = time.time()
    print("Time consumed in working: ", end - start)

    start = time.time()
    res = moocsess.retrieve(base_url)
    end = time.time()
    print("Time consumed in working: ", end - start)


if __name__ == "__main__":
    main()
