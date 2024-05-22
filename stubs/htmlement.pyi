import io
from html.parser import HTMLParser
from typing import Optional
from xml.etree.ElementTree import Element

__all__ = ["HTMLement", "fromstring", "fromstringlist", "parse"]

def fromstring(
    text: str | bytes,
    tag: str = "",
    attrs: Optional[dict[str, str]] = None,
    encoding: Optional[str] = None,
) -> Element: ...
def fromstringlist(
    sequence: str | bytes,
    tag: str = "",
    attrs: Optional[dict[str, str]] = None,
    encoding: Optional[str] = None,
) -> Element: ...
def parse(
    source: str | io.TextIOBase,
    tag: str = "",
    attrs: Optional[dict[str, str]] = None,
    encoding: Optional[str] = None,
) -> Element: ...

class HTMLement:
    encoding: str
    def __init__(
        self,
        tag: str = "",
        attrs: Optional[dict[str, str]] = None,
        encoding: Optional[str] = None,
    ) -> None: ...
    def feed(self, data: str | bytes) -> None: ...
    def close(self) -> Element: ...

class ParseHTML(HTMLParser):
    convert_charrefs: bool
    enabled: bool
    tag: str
    attrs: dict[str, str]
    def __init__(
        self, tag: str = "", attrs: Optional[dict[str, str]] = None
    ) -> None: ...
    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None: ...
    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None: ...
    def handle_endtag(self, tag: str) -> None: ...
    def handle_data(self, data: str) -> None: ...
    def handle_entityref(self, name: str) -> None: ...
    def handle_charref(self, name: str) -> None: ...
    def handle_comment(self, data: str) -> None: ...
    def close(self) -> None: ...
