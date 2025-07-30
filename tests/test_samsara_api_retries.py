import os
import sys
import importlib
import requests

if "samsara_api" in sys.modules:
    del sys.modules["samsara_api"]
SamsaraAPI = importlib.import_module("samsara_api").SamsaraAPI


def _make_response(status: int, body: str = "{}") -> requests.Response:
    resp = requests.Response()
    resp.status_code = status
    resp._content = body.encode()
    return resp


def test_retry_on_failure(monkeypatch):
    attempts = {"count": 0}

    def fake_request(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise requests.ConnectionError("boom")
        return _make_response(200, "{}")

    monkeypatch.setattr(requests, "request", fake_request)
    os.environ["SAMSARA_RETRY_ATTEMPTS"] = "4"
    api = SamsaraAPI("key")
    api.list_drivers()
    assert attempts["count"] == 3


def test_retry_on_http_status(monkeypatch):
    attempts = {"count": 0}

    def fake_request(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] < 2:
            return _make_response(500)
        return _make_response(200)

    monkeypatch.setattr(requests, "request", fake_request)
    os.environ["SAMSARA_RETRY_ATTEMPTS"] = "3"
    api = SamsaraAPI("key")
    api.list_drivers()
    assert attempts["count"] == 2
