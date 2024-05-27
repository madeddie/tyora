from typing import AnyStr, Optional

import html5lib


def find_link(html: AnyStr, xpath: str) -> dict[str, Optional[str]]:
    """Search for html link by xpath and return dict with href and text"""
    anchor_element = html5lib.parse(html, namespaceHTMLElements=False).find(xpath)
    if anchor_element is None:
        return dict()

    link_data: dict[str, Optional[str]] = dict()
    link_data["href"] = anchor_element.get("href")
    link_data["text"] = anchor_element.text

    return link_data


def parse_form(html: AnyStr, xpath: str = ".//form") -> dict[str, Optional[str]]:
    """Search for the first form in html and return dict with action and all other found inputs"""
    form_element = html5lib.parse(html, namespaceHTMLElements=False).find(xpath)
    if form_element is None:
        return dict()

    form_data: dict[str, Optional[str]] = dict()
    form_data["_action"] = form_element.get("action")
    for form_input in form_element.iter("input"):
        form_key = form_input.get("name") or ""
        form_value = form_input.get("value") or ""
        form_data[form_key] = form_value

    return form_data
