import http.server, sys, urllib.parse, mimetypes
from pathlib import Path
HERE = Path(__file__).parent
SHIP = Path(__file__).resolve().parents[2].resolve()
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=str(HERE), **k)
    def do_GET(s):
        p = urllib.parse.unquote(s.path.split("?")[0])
        if p.startswith("/ship/"):
            f = (SHIP / p[6:]).resolve()
            if f.is_relative_to(SHIP) and f.is_file():
                b = f.read_bytes(); s.send_response(200)
                s.send_header("Content-Type", mimetypes.guess_type(f.name)[0] or "application/octet-stream")
                s.send_header("Content-Length", str(len(b))); s.end_headers(); s.wfile.write(b); return
            return s.send_error(404)
        return super().do_GET()
    def end_headers(s): s.send_header("Cache-Control", "no-store"); super().end_headers()
    def log_message(s, *a): pass
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
