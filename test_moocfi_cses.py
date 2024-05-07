import moocfi_cses
import pytest


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


# TODO: functions that use user input or read or write files
def test_create_config(): ...


def test_write_config(): ...


def test_read_config(): ...


def test_get_cookiejar(): ...
