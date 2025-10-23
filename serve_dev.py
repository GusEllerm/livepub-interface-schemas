#!/usr/bin/env python3
import argparse, http.server, socketserver, mimetypes, re, os

mimetypes.add_type('application/ld+json', '.jsonld')
mimetypes.add_type('text/turtle', '.ttl')

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        # Add strong caching for immutable, versioned contexts like /contexts/v1.jsonld
        if re.search(r'/contexts/v\d+\.jsonld$', self.path):
            self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
        super().end_headers()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--port', type=int, default=8000)
    args = ap.parse_args()
    os.chdir(args.root)
    with socketserver.TCPServer(('', args.port), Handler) as httpd:
        print(f"Serving {args.root} at http://localhost:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == '__main__':
    main()
