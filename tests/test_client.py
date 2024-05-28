import pytest
import requests_mock

from tyora.client import Client, TaskState
from tyora.session import MoocfiCsesSession as Session

test_cookies = {"cookie_a": "value_a", "cookie_b": "value_b"}


@pytest.fixture
def mock_session() -> Session:
    return Session(
        base_url="https://example.com",
        cookies=test_cookies,
    )


def test_client(mock_session: Session) -> None:
    client = Client(session=mock_session)

    assert client.session == mock_session


def test_client_get_task_list(mock_session: Session) -> None:
    client = Client(session=mock_session)

    with requests_mock.Mocker() as m:
        m.get(
            "https://example.com/list",
            text=open("tests/test_data/session_logged_in_some_tasks_done.html").read(),
        )
        task_list = client.get_task_list()
    assert len(task_list) == 4
    assert task_list[0].id == "3055"
    assert task_list[0].name == "Candies"
    assert task_list[0].state == TaskState.COMPLETE
    assert task_list[1].id == "3049"
    assert task_list[1].name == "Inversions"
    assert task_list[1].state == TaskState.COMPLETE
    assert task_list[2].id == "3054"
    assert task_list[2].name == "Same bits"
    assert task_list[2].state == TaskState.COMPLETE
    assert task_list[3].id == "2643"
    assert task_list[3].name == "Repeat"
    assert task_list[3].state == TaskState.INCOMPLETE


def test_client_get_task_complete(mock_session: Session) -> None:
    client = Client(session=mock_session)

    with requests_mock.Mocker() as m:
        m.get(
            "https://example.com/task/3055",
            text=open("tests/test_data/task_3055_complete.html").read(),
        )
        task = client.get_task("3055")
    assert task.id == "3055"
    assert task.name == "Candies"
    assert task.state == TaskState.COMPLETE
    assert (
        task.description
        == 'A gummy candy costs a euros and a chocolate candy costs b euros. What is the\nmaximum number of candies you can buy if you have c euros?\n\nYou may assume that a, b and c are integers in the range 1 \\dots 100.\n\nIn a file `candies.py`, implement the function `count` that returns the\nmaximum number of candies.\n\n    \n    \n    def count(a, b, c):\n        # TODO\n    \n    if __name__ == "__main__":\n        print(count(3, 4, 11)) # 3\n        print(count(5, 1, 100)) # 100\n        print(count(2, 3, 1)) # 0\n        print(count(2, 3, 9)) # 4\n    \n\n_Explanation_ : In the first test, a gummy candy costs 3 euros and a chocolate\ncandy costs 4 euros. You can buy at most 3 candies with 11 euros. For example,\ntwo gummy candies and one chocolate candy cost a total of 10 euros leaving you\nwith 1 euro.'
    )
    assert task.submit_link == "/dsa24k/submit/3055/"


def test_client_get_task_incomplete_no_submit_link(mock_session: Session) -> None:
    client = Client(session=mock_session)

    with requests_mock.Mocker() as m:
        m.get(
            "https://example.com/task/3052",
            text=open(
                "tests/test_data/task_3052_incomplete_no_submit_link.html"
            ).read(),
        )
        task = client.get_task("3052")
    assert task.id == "3052"
    assert task.name == "Efficiency test"
    assert task.state == TaskState.INCOMPLETE
    assert (
        task.description
        == "The course material includes two different ways to implement the function\n`count_even`:\n\n    \n    \n    # implementation 1\n    def count_even(numbers):\n        result = 0\n        for x in numbers:\n            if x % 2 == 0:\n                result += 1\n        return result\n    \n    \n    \n    # implementation 2\n    def count_even(numbers):\n        return sum(x % 2 == 0 for x in numbers)\n    \n\nCompare the efficiencies of the two implementations using a list that contains\n10^7 randomly chosen numbers.\n\nIn this exercise, you get a point automatically when you submit the test\nresults and the code that you used.\n\nImplementation 1 run time:  s\n\nImplementation 2 run time:  s\n\nThe code you used in the test:"
    )
    assert task.submit_link is None


def test_client_submit_task(mock_session: Session) -> None:
    client = Client(session=mock_session)

    with requests_mock.Mocker() as m:
        m.post(
            "https://example.com/submit/3055",
            text=open("tests/test_data/submit_3055_success.html").read(),
        )
        result = client.submit_task(
            "3055", "print('Hello, World!')\n", filename="test.py"
        )
    assert result == "Success"
