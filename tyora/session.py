import importlib.metadata
import logging
import os
import sys
from typing import Optional
from urllib.parse import urljoin

import requests
from requests_toolbelt import user_agent

from .utils import find_link, parse_form

HTTP_TIMEOUT = 10
logger = logging.getLogger(__name__)

try:
    __version__ = importlib.metadata.version("tyora")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


class MoocfiCsesSession(requests.Session):
    def __init__(
        self, base_url: str, cookies: Optional[dict[str, str]] = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.base_url = base_url

        if cookies:
            self.cookies.update(cookies)

        self.headers.update(
            {"User-Agent": user_agent(os.path.basename(sys.argv[0]), __version__)}
        )

    def request(self, *args, **kwargs):
        kwargs.setdefault("timeout", HTTP_TIMEOUT)
        return super(MoocfiCsesSession, self).request(*args, **kwargs)

    @property
    def is_logged_in(self) -> bool:
        res = self.get(urljoin(self.base_url, "list"))
        res.raise_for_status()
        logout_link = find_link(res.text, './/a[@title="Log out"]')
        return bool(logout_link)

    def login(self, username: str, password: str) -> None:
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
            action = login_form.pop("_action")
        else:
            logger.debug(
                f"url: {res.url}, status: {res.status_code}\nhtml:\n{res.text}"
            )
            raise ValueError("Failed to find login form")

        login_form["session[login]"] = username
        login_form["session[password]"] = password

        _ = self.post(
            url=urljoin(res.url, action),
            headers={"referer": res.url},
            data=login_form,
        )

        if not self.is_logged_in:
            logger.debug(
                f"url: {res.url}, status: {res.status_code}\nhtml:\n{res.text}"
            )
            raise ValueError("Login failed")
