from tyora import utils


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
        assert utils.find_link(self.valid_html, self.valid_xpath) == self.valid_return

    def test_find_link_bad_xpath(self) -> None:
        assert utils.find_link(self.valid_html, self.invalid_xpath) == {}

    def test_find_link_bad_html(self) -> None:
        assert utils.find_link(self.invalid_html, self.valid_xpath) == {}


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

    def test_parse_form_success(self) -> None:
        assert utils.parse_form(self.valid_html) == {
            "_action": "someaction",
            "somename": "somevalue",
        }

    def test_parse_form_no_form(self) -> None:
        assert utils.parse_form(self.noform_html) == {}

    def test_parse_form_no_input(self) -> None:
        assert utils.parse_form(self.noinput_html) == {"_action": "someaction"}
