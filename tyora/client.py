import logging

from enum import Enum
from dataclasses import dataclass
from typing import AnyStr, Optional
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, tostring

import html5lib
from html2text import html2text

from .session import MoocfiCsesSession as Session
from .utils import parse_form

logger = logging.getLogger(__name__)


class TaskState(Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


@dataclass
class Task:
    id: str
    name: str
    state: TaskState
    description: Optional[str] = None
    code: Optional[str] = None
    submit_file: Optional[str] = None
    submit_link: Optional[str] = None


class Client:
    def __init__(self, session: Session) -> None:
        self.session = session

    def login(self, username: str, password: str) -> None:
        self.session.login(username, password)

    def get_task_list(self) -> list[Task]:
        res = self.session.get(urljoin(self.session.base_url, "list"))
        res.raise_for_status()
        return parse_task_list(res.text)

    def get_task(self, task_id: str) -> Task:
        res = self.session.get(urljoin(self.session.base_url, f"task/{task_id}"))
        res.raise_for_status()
        try:
            task = parse_task(res.text)
        except ValueError as e:
            logger.debug(f"Error parsing task: {e}")
            raise
        return task

    def submit_task(
        self, task_id: str, submission: AnyStr, filename: Optional[str]
    ) -> str:
        task = self.get_task(task_id)
        if not task.submit_file and not filename:
            raise ValueError("No submission filename found")
        if not task.submit_link:
            raise ValueError("No submit link found")
        submit_file = task.submit_file or filename

        res = self.session.get(urljoin(self.session.base_url, task.submit_link))
        res.raise_for_status()
        parsed_form_data = parse_form(res.text)
        action = parsed_form_data.pop("_action")

        submit_form_data = dict()
        for key, value in parsed_form_data.items():
            submit_form_data[key] = (None, value)
        submit_form_data["file"] = (submit_file, submission)
        submit_form_data["lang"] = (None, "Python3")
        submit_form_data["option"] = (None, "CPython3")
        res = self.session.post(
            urljoin(self.session.base_url, action), files=submit_form_data
        )
        res.raise_for_status()

        return res.url


def parse_task_list(html: AnyStr) -> list[Task]:
    """Parse html to find tasks and their status, returns list of Task objects"""
    root = html5lib.parse(html, namespaceHTMLElements=False)
    task_element_list = root.findall('.//li[@class="task"]')

    task_list = list()
    for task_element in task_element_list:
        task_id = None
        task_name = None
        task_state = None

        task_link = task_element.find("a")
        if task_link is None:
            continue

        task_name = task_link.text
        task_id = task_link.get("href", "/").split("/")[-1]
        if not task_name or not task_id:
            continue

        task_element_spans = task_element.findall("span")
        if not task_element_spans:
            continue

        task_element_span = next(
            (span for span in task_element_spans if span.get("class", "") != "detail"),
            None,
        )
        if task_element_span is not None:
            task_element_class = task_element_span.get("class") or ""

        task_state = (
            TaskState.COMPLETE if "full" in task_element_class else TaskState.INCOMPLETE
        )

        task = Task(
            id=task_id,
            name=task_name,
            state=task_state,
        )
        task_list.append(task)

    return task_list


def parse_task(html: AnyStr) -> Task:
    root = html5lib.parse(html, namespaceHTMLElements=False)
    task_link_element = root.find('.//div[@class="nav sidebar"]/a')
    task_link = task_link_element if task_link_element is not None else Element("a")
    task_id = task_link.get("href", "").split("/")[-1]
    if not task_id:
        raise ValueError("Failed to find task id")
    task_name = task_link.text or None
    if not task_name:
        raise ValueError("Failed to find task name")
    task_span_element = task_link.find("span")
    task_span = task_span_element if task_span_element is not None else Element("span")
    task_span_class = task_span.get("class", "")
    desc_div_element = root.find('.//div[@class="md"]')
    desc_div = desc_div_element if desc_div_element is not None else Element("div")
    description = html2text(tostring(desc_div).decode("utf8"))
    code = root.findtext(".//pre", None)
    submit_link_element = root.find('.//a[.="Submit"]')
    submit_link = (
        submit_link_element.get("href", None)
        if submit_link_element is not None
        else None
    )

    submit_file = next(
        iter(
            [
                code_element.text
                for code_element in root.findall(".//code")
                if code_element.text is not None and ".py" in code_element.text
            ]
        ),
        None,
    )
    task = Task(
        id=task_id,
        name=task_name,
        state=TaskState.COMPLETE if "full" in task_span_class else TaskState.INCOMPLETE,
        description=description.strip(),
        code=code,
        submit_file=submit_file,
        submit_link=submit_link,
    )

    return task


# def submit_task(task_id: str, filename: str) -> None:
#     """submit file to the submit form or task_id"""
#     html = session.http_request(urljoin(base_url, f"task/{task_id}"))
#     task = parse_task(html)
#     answer = input("Do you want to submit this task? (y/n): ")
#     if answer in ('y', 'Y'):
#         with open(filename, 'r') as f:


# TODO test with failing results
# Seems to be broken since the switch to html5lib, needs tests!
def parse_submit_result(html: AnyStr) -> dict[str, str]:
    root = html5lib.parse(html, namespaceHTMLElements=False)
    submit_status_element = root.find('.//td[.="Status:"]/..') or Element("td")
    submit_status_span_element = submit_status_element.find("td/span") or Element(
        "span"
    )
    submit_status = submit_status_span_element.text or ""
    submit_result_element = root.find('.//td[.="Result:"]/..') or Element("td")
    submit_result_span_element = submit_result_element.find("td/span") or Element(
        "span"
    )
    submit_result = submit_result_span_element.text or ""

    return {
        "status": submit_status.lower(),
        "result": submit_result.lower(),
    }
