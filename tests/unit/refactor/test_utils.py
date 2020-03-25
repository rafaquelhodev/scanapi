import pytest
import requests

from scanapi.refactor.utils import join_urls, hide_sensitive_info, _hide, _override_info


@pytest.fixture
def response(requests_mock):
    requests_mock.get("http://test.com", text="data")
    return requests.get("http://test.com")


class TestJoinUrls:
    test_data = [
        (
            "http://demo.scanapi.dev/api/",
            "health",
            "http://demo.scanapi.dev/api/health",
        ),
        (
            "http://demo.scanapi.dev/api/",
            "/health",
            "http://demo.scanapi.dev/api/health",
        ),
        (
            "http://demo.scanapi.dev/api/",
            "/health/",
            "http://demo.scanapi.dev/api/health/",
        ),
        ("http://demo.scanapi.dev/api", "health", "http://demo.scanapi.dev/api/health"),
        (
            "http://demo.scanapi.dev/api",
            "/health",
            "http://demo.scanapi.dev/api/health",
        ),
        (
            "http://demo.scanapi.dev/api",
            "/health/",
            "http://demo.scanapi.dev/api/health/",
        ),
        (
            "",
            "http://demo.scanapi.dev/api/health/",
            "http://demo.scanapi.dev/api/health/",
        ),
        (
            "http://demo.scanapi.dev/api/health/",
            "",
            "http://demo.scanapi.dev/api/health/",
        ),
        ("", "", ""),
    ]

    @pytest.mark.parametrize("url_1, url_2, expected", test_data)
    def test_build_url_properly(self, url_1, url_2, expected):
        assert join_urls(url_1, url_2) == expected


class TestHideSensitiveInfo:
    @pytest.fixture
    def mock__hide(self, mocker):
        return mocker.patch("scanapi.refactor.utils._hide")

    test_data = [
        ({}, {}, {}),
        ({"report": {"abc": "def"}}, {}, {}),
        ({"report": {"hide-request": {"headers": ["abc"]}}}, {"headers": ["abc"]}, {}),
        ({"report": {"hide-response": {"headers": ["abc"]}}}, {}, {"headers": ["abc"]}),
    ]

    @pytest.mark.parametrize("settings, request_settings, response_settings", test_data)
    def test_calls__hide(
        self,
        settings,
        request_settings,
        response_settings,
        mocker,
        response,
        mock__hide,
    ):
        mocker.patch("scanapi.refactor.utils.SETTINGS", settings)
        hide_sensitive_info(response)

        calls = [
            mocker.call(response.request, request_settings),
            mocker.call(response, response_settings),
        ]

        mock__hide.assert_has_calls(calls)


class TestHide:
    @pytest.fixture
    def mock__override_info(self, mocker):
        return mocker.patch("scanapi.refactor.utils._override_info")

    test_data = [
        ({}, []),
        ({"headers": ["abc", "def"]}, [("headers", "abc"), ("headers", "def")]),
        ({"headers": ["abc"]}, [("headers", "abc")]),
    ]

    @pytest.mark.parametrize("settings, calls", test_data)
    def test_calls__override_info(
        self, settings, calls, mocker, response, mock__override_info
    ):
        _hide(response, settings)
        calls = [mocker.call(response, call[0], call[1]) for call in calls]

        mock__override_info.assert_has_calls(calls)


class TestOverrideInfo:
    def test_overrides(self, response):
        response.headers = {"abc": "123"}
        http_attr = "headers"
        secret_field = "abc"

        _override_info(response, http_attr, secret_field)

        assert response.headers["abc"] == "<sensitive_information>"

    def test_when_http_attr_is_not_allowed(self, response, mocker):
        mocker.patch("scanapi.refactor.utils.ALLOWED_ATTRS_TO_HIDE", ["body"])
        response.headers = {"abc": "123"}
        http_attr = "headers"
        secret_field = "abc"

        _override_info(response, http_attr, secret_field)

        assert response.headers["abc"] == "123"

    def test_when_http_attr_does_not_have_the_field(self, response, mocker):
        mocker.patch("scanapi.refactor.utils.ALLOWED_ATTRS_TO_HIDE", ["body"])
        response.headers = {"abc": "123"}
        http_attr = "headers"
        secret_field = "def"

        _override_info(response, http_attr, secret_field)

        assert response.headers == {"abc": "123"}
