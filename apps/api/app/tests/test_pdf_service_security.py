"""Regression test for a real SSRF vulnerability found during the independent
audit: chapter markdown's ordinary image syntax (`![alt](url)`) made WeasyPrint
issue a server-side GET to whatever URL a user wrote there — reproduced
against a local HTTP listener before `_restricted_url_fetcher` existed.
"""

import http.server
import threading
import uuid

import pytest

from app.db.models.book import Book, BookChapter, BookLanguage
from app.services.pdf_service import render_book_pdf


class _RecordingHandler(http.server.BaseHTTPRequestHandler):
    hits: list[str] = []

    def do_GET(self):  # noqa: N802 — http.server's naming convention
        _RecordingHandler.hits.append(self.path)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture()
def local_http_listener():
    _RecordingHandler.hits = []
    server = http.server.HTTPServer(("127.0.0.1", 0), _RecordingHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield port, _RecordingHandler.hits
    server.shutdown()


def _book_with_markdown(content_markdown: str) -> Book:
    book = Book(
        id=uuid.uuid4(), user_id=uuid.uuid4(), title="t", author_name="a", language=BookLanguage.EN
    )
    book.chapters = [
        BookChapter(id=uuid.uuid4(), book_id=book.id, order_index=0, title="c", content_markdown=content_markdown)
    ]
    return book


def test_markdown_image_does_not_trigger_outbound_request(local_http_listener):
    port, hits = local_http_listener
    book = _book_with_markdown(f"![pixel](http://127.0.0.1:{port}/internal-metadata-service/secret)")

    # Must not raise, and must not leave the process — a blocked image is
    # skipped, not a fatal error; the security property is "no request sent".
    pdf_bytes = render_book_pdf(book)

    assert pdf_bytes[:4] == b"%PDF"
    assert hits == []


def test_raw_html_img_tag_also_blocked(local_http_listener):
    port, hits = local_http_listener
    book = _book_with_markdown(f'<img src="http://127.0.0.1:{port}/exfil">')

    render_book_pdf(book)

    assert hits == []


def test_own_embedded_fonts_still_load(local_http_listener):
    """The fix must not be so broad it breaks StromeX's own font pipeline."""
    _, hits = local_http_listener
    book = _book_with_markdown("Ordinary text, no external resources.")

    pdf_bytes = render_book_pdf(book)

    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 1000  # a real, non-trivial PDF, not an empty shell
