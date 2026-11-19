import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from tests.test_link_analysis import SAMPLE_PAYLOAD


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        self.rfile.read(length)
        body = {
            "id": "mock-local-provider",
            "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": json.dumps(SAMPLE_PAYLOAD)}}],
            "usage": {"prompt_tokens": 5000, "completion_tokens": 1600, "total_tokens": 6600},
        }
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 4010), Handler).serve_forever()
