import pytest
import requests_mock
from tyora.session import MoocfiCsesSession as Session

test_cookies = {"cookie_a": "value_a", "cookie_b": "value_b"}


@pytest.fixture
def mock_session() -> Session:
    return Session(
        base_url="https://example.com",
        cookies=test_cookies,
    )


def test_login_successful(mock_session: Session) -> None:
    # Mocking the HTTP response for successful login
    with requests_mock.Mocker() as m:
        m.get(
            "https://example.com/list",
            text=open("tests/test_data/session_logged_in.html").read(),
        )
        mock_session.login(username="test_user@test.com", password="test_password")
        print(mock_session.get("https://example.com/list").text)
        assert mock_session.is_logged_in


def test_login_failed(mock_session: Session) -> None:
    # Mocking the HTTP response for failed login
    with requests_mock.Mocker() as m:
        m.get(
            "https://example.com/list",
            text=open("tests/test_data/session_logged_out.html").read(),
        )
        m.get(
            "https://example.com/login/oauth-redirect?site=mooc.fi",
            text=open("tests/test_data/tmcmoocfi-oauth-redirect.html").read(),
        )
        m.post(
            "https://example.com/sessions",
            text=open("tests/test_data/tmcmoocfi-sessions.html").read(),
        )
        with pytest.raises(ValueError):
            mock_session.login(username="test_user@test.com", password="test_password")


def test_loading_cookies(mock_session: Session) -> None:
    assert mock_session.cookies.get_dict() == test_cookies
