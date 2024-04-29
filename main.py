from html.parser import HTMLParser
import json
import urllib.parse

import requests

base_url = "https://cses.fi/dsa24k/list/"


class LinkFinderParser(HTMLParser):
    def __init__(self, attr_key: str, attr_value: str) -> None:
        HTMLParser.__init__(self)
        self.link = str()
        self.attr_key = attr_key
        self.attr_value = attr_value

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        href = None
        is_valid = False
        if tag == "a":
            for attr in attrs:
                if attr[0] == self.attr_key and attr[1] == self.attr_value:
                    is_valid = True
                elif attr[0] == "href":
                    href = attr[1]

            if is_valid:
                self.link = href


class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.action = str()
        self.form = dict()
        self.record = False

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
            self.record == False


def login(login: str, password: str) -> requests.sessions.Session:
    session = requests.Session()
    res = session.get(base_url)

    parser = LinkFinderParser("class", "account")
    parser.feed(res.text)
    login_url = urllib.parse.urljoin(res.url, parser.link)
    session.headers.update({"referer": res.url})
    res = session.get(login_url)

    parser = FormParser()
    parser.feed(res.text)
    form_data = parser.form
    form_data["session[login]"] = login
    form_data["session[password]"] = password
    session.headers.update({"referer": res.url})
    res = session.post(urllib.parse.urljoin(res.url, parser.action), data=form_data)

    return session


def read_config():
    config_file = "moocfi_cses.json"
    with open(config_file, "r") as f:
        config = json.load(f)
    return config


def main():
    config = read_config()
    session = login(config["username"], config["password"])

    res = session.get(base_url)
    # soup = BeautifulSoup(res.text, 'html.parser')
    # print(soup.find('a', class_='account').string)
    #
    # for item in soup.find_all('li', class_='task'):
    #     completed = '✅' if 'full' in item.find('span', class_='task-score')['class'] else '❌'
    #     print(completed, item.a.get('href'), item.a.string)

    print(res, res.text)


if __name__ == "__main__":
    main()
