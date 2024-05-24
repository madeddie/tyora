import pytest
from tyora import tyora


def test_parse_args_missing_args() -> None:
    with pytest.raises(SystemExit):
        tyora.parse_args()


def test_parse_args_command() -> None:
    args = tyora.parse_args(["list"])
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

    def test_find_link_success(self) -> None:
        assert tyora.find_link(self.valid_html, self.valid_xpath) == self.valid_return

    def test_find_link_bad_xpath(self) -> None:
        assert tyora.find_link(self.valid_html, self.invalid_xpath) == {}

    def test_find_link_bad_html(self) -> None:
        assert tyora.find_link(self.invalid_html, self.valid_xpath) == {}


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


# TODO: functions that use user input or read or write files
def test_create_config() -> None: ...


def test_write_config() -> None: ...


def test_read_config() -> None: ...


def test_get_cookiejar() -> None: ...
