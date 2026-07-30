#!/usr/bin/env python3
"""Serves apps/web/out with the same extensionless-path fallback that
MainActivity.candidatePaths() implements for the real Android WebView
(try path.html, then path/index.html, then the raw path) — so this
browser-based functional test exercises the same asset-resolution logic
the shipped app uses, not just the raw files a plain static server would."""
import http.server
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4173


class FallbackHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        clean = path.lstrip("/")
        if clean == "" or "." in os.path.basename(clean):
            return super().translate_path(path)
        for candidate in (clean + ".html", clean.rstrip("/") + "/index.html"):
            if os.path.isfile(os.path.join(ROOT, candidate)):
                return super().translate_path("/" + candidate)
        return super().translate_path(path)


if __name__ == "__main__":
    http.server.test(HandlerClass=FallbackHandler, port=PORT, bind="127.0.0.1")
