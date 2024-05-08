import moocfi_cses
import pytest
import requests_mock


def test_parse_args_missing_args():
    with pytest.raises(SystemExit):
        moocfi_cses.parse_args()


def test_parse_args_command():
    args = moocfi_cses.parse_args(["list"])
    assert args.cmd == "list"


class TestFindLink:
    valid_html = (
        "<html><body>"
        '<a href="somelink" class="someclass">sometext</a>'
        "</body></html>"
    )
    invalid_html = "<html><body>No links here</body></html>"
    valid_xpath = './/a[@class="someclass"]'
    invalid_xpath = './/a[@class="somethingelse"]'
    valid_return = {"href": "somelink", "text": "sometext"}

    def test_find_link_success(self):
        assert (
            moocfi_cses.find_link(self.valid_html, self.valid_xpath)
            == self.valid_return
        )

    def test_find_link_bad_xpath(self):
        assert moocfi_cses.find_link(self.valid_html, self.invalid_xpath) == {}

    def test_find_link_bad_html(self):
        assert moocfi_cses.find_link(self.invalid_html, self.valid_xpath) == {}


class TestParseForm:
    valid_html = (
        '<html><body><form action="someaction">'
        '<input name="somename" value="somevalue">sometext</input>'
        "</form></body></html>"
    )
    noform_html = "<html><body>No form here</body></html>"
    noinput_html = (
        '<html><body><form action="someaction">Nothing here</form></body></html>'
    )


# TODO: verify these mocked tests are actually accurate
# TODO: add tests for unreachable and failing endpoints, 4xx, 5xx, etc
@pytest.fixture
def mock_session():
    return moocfi_cses.Session(username="test_user@test.com", password="test_password", base_url="https://example.com")

def test_login_successful(mock_session):
    # Mocking the HTTP response for successful login
    with requests_mock.Mocker() as m:
        m.get("https://example.com", text='<a class="account" href="/user/1234">test_user@test.com (mooc.fi)</a>')
        mock_session.login()
        assert mock_session.is_logged_in

def test_login_failed(mock_session):
    # Mocking the HTTP response for failed login
    with requests_mock.Mocker() as m:
        m.get("https://example.com", text='<a class="account" href="/login/oauth-redirect?site=mooc.fi">Login using mooc.fi</a>')
        m.get("https://example.com/account", text="Login required")
        m.get("https://example.com/login/oauth-redirect?site=mooc.fi", text="")
        with pytest.raises(ValueError):
            mock_session.login()

# TODO: functions that use user input or read or write files
def test_create_config(): ...


def test_write_config(): ...


def test_read_config(): ...


def test_get_cookiejar(): ...