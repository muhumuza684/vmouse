import socket
import urllib.error
import urllib.request

import pytest

import web_static

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never use a proxy for localhost


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture()
def site(tmp_path):
    pwa = tmp_path / "pwa"
    pwa.mkdir()
    (pwa / "index.html").write_text("<h1>hello</h1>")
    (pwa / "sub").mkdir()
    (tmp_path / "secret.txt").write_text("do not serve")
    port = free_port()
    server = web_static.serve_http(pwa, port)
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


def get(url):
    try:
        with OPENER.open(url, timeout=3) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def test_serves_the_page(site):
    status, body = get(site + "/")
    assert status == 200 and b"hello" in body


def test_other_files_and_traversal_are_refused(site):
    for path in ("/secret.txt", "/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt", "/nothing"):
        assert get(site + path)[0] == 404, path


def test_no_directory_listing(site):
    assert get(site + "/sub/")[0] == 404
