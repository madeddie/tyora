import importlib.metadata
import logging
import os
import sys
from typing import AnyStr, Optional
from urllib.parse import urljoin

import html5lib
import requests
from requests_toolbelt import user_agent

logger = logging.getLogger(__name__)

try:
    __version__ = importlib.metadata.version("tyora")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


class MoocfiCsesSession(requests.Session):
    def __init__(
        self,
        username: str,
        password: str,
        base_url: str,
        cookies: Optional[dict] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.username = username
        self.password = password
        self.base_url = base_url

        if cookies:
            self.cookies.update(cookies)

        self.headers.update(
            {"User-Agent": user_agent(os.path.basename(sys.argv[0]), __version__)}
        )

    @property
    def is_logged_in(self) -> bool:
        res = self.get(urljoin(self.base_url, "list"))
        res.raise_for_status()
        login_link = find_link(res.text, './/a[@class="account"]')
        login_text = login_link.get("text") or ""
        return self.username in login_text

    def login(self) -> None:
        """Log into the site using webscraping

        Steps:
        - checks if already logged in
        - retrieves base URL
        - finds and retrieves login URL
        - finds and submits login form
        - checks if logged in
        """
        if self.is_logged_in:
            return

        res = self.get(urljoin(self.base_url, "list"))
        res.raise_for_status()
        login_link = find_link(res.text, './/a[@class="account"]')
        if login_link:
            login_url = urljoin(res.url, login_link.get("href"))
        else:
            logger.debug(
                f"url: {res.url}, status: {res.status_code}\nhtml:\n{res.text}"
            )
            raise ValueError("Failed to find login url")

        res = self.get(login_url, headers={"referer": res.url})
        login_form = parse_form(res.text, ".//form")
        if login_form:
            action = login_form.get("_action")
            login_form.pop("_action")
        else:
            logger.debug(
                f"url: {res.url}, status: {res.status_code}\nhtml:\n{res.text}"
            )
            raise ValueError("Failed to find login form")

        login_form["session[login]"] = self.username
        login_form["session[password]"] = self.password

        self.post(
            url=urljoin(res.url, action),
            headers={"referer": res.url},
            data=login_form,
        )

        if not self.is_logged_in:
            logger.debug(
                f"url: {res.url}, status: {res.status_code}\nhtml:\n{res.text}"
            )
            raise ValueError("Login failed")


def find_link(html: AnyStr, xpath: str) -> dict[str, Optional[str]]:
    """Search for html link by xpath and return dict with href and text"""
    anchor_element = html5lib.parse(html, namespaceHTMLElements=False).find(xpath)
    if anchor_element is None:
        return dict()

    link_data = dict()
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
