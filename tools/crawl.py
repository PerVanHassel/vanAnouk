#!/usr/bin/env python3
"""Polite crawler that mirrors vananouk.nl byte-for-byte into RAW_DIR.

- Only fetches URLs on vananouk.nl.
- Waits between requests; when the host's rate-limit page appears it backs
  off and retries later instead of trying to get around it.
- Writes a manifest (url -> local file, status, content type, final url).
"""
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse as up
from collections import deque

RAW_DIR = sys.argv[1]
STATE = os.path.join(RAW_DIR, '_manifest.json')
HOST = 'vananouk.nl'
BASE = 'https://vananouk.nl'
DELAY = float(os.environ.get('DELAY', '2.5'))
UA = 'vanAnouk-site-backup/1.0 (owner-authorized mirror)'

SEEDS = [
    '/', '/about/', '/contact/', '/portfolio/', '/boeken/', '/magazines/',
    '/educatieve-uitgaven/', '/logo-en-huisstijl/', '/voorbeeld-pagina/',
    '/qode-test/', '/99-2/', '/2019/03/13/hallo-wereld/', '/2018/03/19/hello-world/',
    '/wp-json/wp/v2/pages?per_page=100', '/wp-json/wp/v2/posts?per_page=100',
    '/wp-json/wp/v2/media?per_page=100&page=1',
    '/wp-json/wp/v2/media?per_page=100&page=2',
    '/wp-json/wp/v2/media?per_page=100&page=3',
    '/deze-pagina-bestaat-niet-404/',
]

SKIP_PATH = re.compile(
    r'^/(wp-admin|wp-login\.php|xmlrpc\.php|wp-cron\.php|feed|comments/feed|'
    r'wp-json/oembed|wp-json/contact-form-7|wp-json/?$|wp-includes/wlwmanifest\.xml)'
    r'|/feed/?$|/embed/?$|/trackback/?$')
ASSET_EXT = re.compile(
    r'\.(css|js|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot|otf|pdf|mp4|webm|mp3|'
    r'json|xml|txt|map|swf|cur)$', re.I)

URL_IN_TEXT = re.compile(r'(?:https?:)?(?:\\/|/){2}(?:www\.)?vananouk\.nl(?:\\/|/)[^\s"\'<>()]*')
ATTR = re.compile(
    r'\s(?:href|src|data-[\w-]+|poster|content|action|srcset|data-srcset)\s*=\s*(["\'])(.*?)\1',
    re.I | re.S)
CSS_URL = re.compile(r'url\(\s*([\'"]?)([^\'")]+)\1\s*\)', re.I)
CSS_IMPORT = re.compile(r'@import\s+([\'"])([^\'"]+)\1', re.I)


def is_challenge(body: bytes) -> bool:
    # The host's rate-limit page comes in several languages ("One moment,
    # please...", "Even geduld..."); its markup is the same.
    return b'class="throbber"' in body and b'window.location.reload()' in body


def norm(url, base):
    url = html.unescape(url.strip()).replace('\\/', '/')
    if not url or url.startswith(('data:', 'mailto:', 'tel:', 'javascript:', '#')):
        return None
    url = up.urljoin(base, url)
    p = up.urlsplit(url)
    if p.scheme not in ('http', 'https'):
        return None
    if p.hostname not in (HOST, 'www.' + HOST):
        return None
    path = p.path or '/'
    return up.urlunsplit(('https', HOST, path, p.query, ''))


def local_name(url, ctype):
    p = up.urlsplit(url)
    path = up.unquote(p.path)
    if path.endswith('/'):
        path += 'index.html'
    elif not os.path.splitext(path)[1]:
        path += '/index.html' if 'html' in ctype else ''
    if p.query and (path.endswith('.php') or path.startswith('/wp-json') or
                    not ASSET_EXT.search(path)):
        h = hashlib.sha1(p.query.encode()).hexdigest()[:10]
        ext = '.json' if 'json' in ctype else ('.html' if 'html' in ctype else '')
        path = path.rstrip('/') + '__q_' + h + ext
    return path.lstrip('/')


def fetch(url, out):
    tries = 0
    while True:
        cmd = ['curl', '-sS', '-L', '--max-redirs', '5', '-m', '90', '-A', UA,
               '-H', 'Accept-Language: nl-NL,nl;q=0.9',
               '-o', out, '-w', '%{http_code}\t%{url_effective}\t%{content_type}', url]
        r = subprocess.run(cmd, capture_output=True, text=True)
        time.sleep(DELAY)
        if r.returncode != 0:
            tries += 1
            print('  curl error', r.returncode, r.stderr.strip()[:200], flush=True)
            if tries > 4:
                return None
            time.sleep(10 * tries)
            continue
        code, final, ctype = (r.stdout.split('\t') + ['', '', ''])[:3]
        body = open(out, 'rb').read()
        if is_challenge(body):
            tries += 1
            wait = min(60 * tries, 300)
            print(f'  rate-limit page, backing off {wait}s (try {tries})', flush=True)
            if tries > 8:
                return None
            time.sleep(wait)
            continue
        return int(code), final, ctype


def extract(url, body, ctype):
    text = body.decode('utf-8', 'replace')
    found = set()
    if 'css' in ctype or url.split('?')[0].endswith('.css'):
        for m in CSS_URL.finditer(text):
            found.add(m.group(2))
        for m in CSS_IMPORT.finditer(text):
            found.add(m.group(2))
    elif 'html' in ctype:
        for m in ATTR.finditer(text):
            v = m.group(2)
            if ',' in v and re.search(r'\s\d+[wx]\b', v):
                for part in v.split(','):
                    found.add(part.strip().split(' ')[0])
            else:
                found.add(v)
        for m in CSS_URL.finditer(text):
            found.add(m.group(2))
    elif 'javascript' in ctype or url.split('?')[0].endswith('.js'):
        pass
    if 'json' not in ctype:
        for m in URL_IN_TEXT.finditer(text):
            found.add(m.group(0).rstrip('\\'))
    if 'json' in ctype:
        try:
            data = json.loads(text)
            items = data if isinstance(data, list) else [data]
            for it in items:
                if isinstance(it, dict):
                    if it.get('source_url'):
                        found.add(it['source_url'])
                    for s in ((it.get('media_details') or {}).get('sizes') or {}).values():
                        if isinstance(s, dict) and s.get('source_url'):
                            found.add(s['source_url'])
                    if it.get('link'):
                        found.add(it['link'])
        except Exception:
            pass
    out = set()
    for f in found:
        f = f.strip()
        if not f or ' ' in f:
            continue
        if not (f.startswith(('http', '/', '.', '\\/')) or ASSET_EXT.search(f.split('?')[0])):
            continue
        n = norm(f, url)
        if n:
            out.add(n)
    return out


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    q = deque()
    seen = set(state)
    extra = sys.argv[2:]
    for s in SEEDS + extra:
        u = norm(s, BASE + '/')
        if u and u not in seen:
            q.append(u)
            seen.add(u)
    # re-queue links of already-fetched files so a resumed run continues
    for u, rec in list(state.items()):
        if rec.get('file') and os.path.exists(os.path.join(RAW_DIR, rec['file'])):
            body = open(os.path.join(RAW_DIR, rec['file']), 'rb').read()
            for n in extract(rec.get('final') or u, body, rec.get('ctype', '')):
                if n not in seen:
                    seen.add(n)
                    q.append(n)
    while q:
        u = q.popleft()
        path = up.urlsplit(u).path
        qry = up.urlsplit(u).query
        is_seed = any(u == norm(x, BASE + '/') for x in SEEDS)
        if SKIP_PATH.search(path) or (not is_seed and (path.startswith('/wp-json') or
                (qry and not ASSET_EXT.search(path)))):
            state[u] = {'skipped': True}
            continue
        tmp = os.path.join(RAW_DIR, '_tmp_download')
        print(f'[{len(state)}/{len(state) + len(q)}] {u}', flush=True)
        res = fetch(u, tmp)
        if res is None:
            state[u] = {'error': True}
            json.dump(state, open(STATE, 'w'), indent=1)
            continue
        code, final, ctype = res
        name = local_name(final if final else u, ctype)
        dest = os.path.join(RAW_DIR, name)
        os.makedirs(os.path.dirname(dest) or RAW_DIR, exist_ok=True)
        if os.path.isdir(dest):
            dest = os.path.join(dest, 'index.html')
            name = os.path.join(name, 'index.html')
        os.replace(tmp, dest)
        state[u] = {'status': code, 'final': final, 'ctype': ctype, 'file': name}
        if code < 400 or u.endswith('deze-pagina-bestaat-niet-404/'):
            body = open(dest, 'rb').read()
            for n in extract(final or u, body, ctype):
                if n not in seen:
                    seen.add(n)
                    q.append(n)
        json.dump(state, open(STATE, 'w'), indent=1)
    print('DONE', len(state), flush=True)


if __name__ == '__main__':
    main()
