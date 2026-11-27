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
            global PENALTY, STREAK
            PENALTY = min(max(90, PENALTY * 2), 600)
            STREAK = 0
            wait = PENALTY
            print(f'  rate-limit page, backing off {wait}s (try {tries})', flush=True)
            if tries > 8:
                return None
            time.sleep(wait)
            continue
        STREAK_OK()
        return int(code), final, ctype


PENALTY = 0
STREAK = 0


def STREAK_OK():
    global PENALTY, STREAK
    STREAK += 1
    if STREAK >= 25:
        PENALTY = PENALTY // 2
        STREAK = 0


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
    """Fetch the pages and files the site itself uses first ("core"), then
    the extra files only listed by the media library (attachment pages and
    every generated image size)."""
    os.makedirs(RAW_DIR, exist_ok=True)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    core, extra_q = deque(), deque()
    seen, low = set(state), set()
    seeds = [norm(s, BASE + '/') for s in SEEDS + sys.argv[2:]]

    def add(n, is_low):
        if n in seen:
            if not is_low and n in low:
                low.discard(n)  # promoted; still queued in extra_q, harmless
                core.append(n)
            return
        seen.add(n)
        if is_low:
            low.add(n)
            extra_q.append(n)
        else:
            core.append(n)

    def links_of(u, rec):
        f = rec.get('file')
        if not f or not os.path.exists(os.path.join(RAW_DIR, f)):
            return set()
        body = open(os.path.join(RAW_DIR, f), 'rb').read()
        return extract(rec.get('final') or u, body, rec.get('ctype', ''))

    # replay what is already on disk to rebuild both queues
    queue = deque((s, False) for s in seeds if s)
    replayed = set()
    while queue:
        u, is_low = queue.popleft()
        if (u, is_low) in replayed:
            continue
        replayed.add((u, is_low))
        if u not in state:
            seen.discard(u)
            add(u, is_low)
            continue
        child_low = is_low or 'json' in state[u].get('ctype', '')
        for n in links_of(u, state[u]):
            if not is_low or n not in [x for x, _ in replayed]:
                queue.append((n, child_low))
    for u in list(core) + list(extra_q):
        seen.add(u)

    while core or extra_q:
        if core:
            u, is_low = core.popleft(), False
        else:
            u, is_low = extra_q.popleft(), True
        if u in state:
            continue
        path = up.urlsplit(u).path
        qry = up.urlsplit(u).query
        is_seed = u in seeds
        if SKIP_PATH.search(path) or (not is_seed and (path.startswith('/wp-json') or
                (qry and not ASSET_EXT.search(path)))):
            state[u] = {'skipped': True}
            continue
        tmp = os.path.join(RAW_DIR, '_tmp_download')
        tag = 'extra' if is_low else 'core'
        print(f'[{len(state)}] ({tag}: core left {len(core)}, extra left {len(extra_q)}) {u}', flush=True)
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
        state[u] = {'status': code, 'final': final, 'ctype': ctype, 'file': name,
                    'core': not is_low}
        if code < 400 or u.endswith('deze-pagina-bestaat-niet-404/'):
            child_low = is_low or 'json' in ctype
            for n in extract(final or u, open(dest, 'rb').read(), ctype):
                add(n, child_low)
        json.dump(state, open(STATE, 'w'), indent=1)
        if not core and not is_low:
            print('CORE DONE', flush=True)
    print('DONE', len(state), flush=True)


if __name__ == '__main__':
    main()
