#!/usr/bin/env python3
"""Turn the raw mirror into a self-contained static site.

Every https://vananouk.nl/... reference that points to a mirrored file (or to
anything under /wp-content/ or /wp-includes/) is rewritten to a relative path,
so the copy works on any host and from a local web server. Nothing else in the
markup is touched. Head links that describe the canonical address of a page
(canonical, shortlink, oEmbed, RSS, pingback, RSD...) keep their absolute URL.
"""
import html
import json
import os
import posixpath
import re
import shutil
import sys
import urllib.parse as up

RAW, OUT, DATA = sys.argv[1], sys.argv[2], sys.argv[3]
manifest = json.load(open(os.path.join(RAW, '_manifest.json')))
HOST = 'vananouk.nl'
NOTFOUND_KEY = 'https://vananouk.nl/deze-pagina-bestaat-niet-404/'

URL_RE = re.compile(
    r'(?P<url>(?:https?:)?(?:\\/|/){2}(?:www\.)?vananouk\.nl(?![\w.-])(?:(?:\\/|/)[^\s"\'<>()\\]*(?:\\/[^\s"\'<>()\\]*)*)?)')
KEEP_TAG = re.compile(
    r'<link\b[^>]*\brel=["\'](?:canonical|shortlink|alternate|pingback|EditURI|wlwmanifest|'
    r'https://api\.w\.org/|profile)["\'][^>]*>|<meta\b[^>]*\bproperty=["\']og:url["\'][^>]*>',
    re.I)

# url (no fragment) -> output path (relative to OUT)
url_map = {}
files = {}  # raw file -> output path
data_names = {}
for url, rec in manifest.items():
    f = rec.get('file')
    if not f:
        continue
    st = rec.get('status', 0)
    if url == NOTFOUND_KEY:
        files[f] = '404.html'
        continue
    if f.startswith('wp-json/'):
        files[f] = None  # goes to DATA, not into the site
        q = up.parse_qs(up.urlsplit(url).query)
        kind = up.urlsplit(url).path.rstrip('/').split('/')[-1]
        data_names[f] = kind + ('-page' + q['page'][0] if 'page' in q else '') + '.json'
        continue
    if st >= 400:
        continue
    files[f] = f
    for u in (url, rec.get('final') or url):
        url_map[u] = f


def canon(u):
    u = html.unescape(u).replace('\\/', '/')
    if u.startswith('//'):
        u = 'https:' + u
    p = up.urlsplit(u)
    path = p.path or '/'
    return up.urlunsplit(('https', HOST, path, p.query, '')), p.fragment


def rel(from_file, target, root_relative):
    pretty = target.endswith('index.html')
    tdir = posixpath.dirname(target) if pretty else target
    if root_relative:
        out = '/' + (tdir + '/' if pretty and tdir else tdir)
        return out if out != '//' else '/'
    start = posixpath.dirname(from_file) or '.'
    if pretty:
        r = posixpath.relpath(tdir or '.', start)
        return ('./' if r == '.' else r + '/')
    return posixpath.relpath(target, start)


def resolve(u):
    """Return (output path, keep_query) or None."""
    full, frag = canon(u)
    if full in url_map:
        return url_map[full], frag, ''
    p = up.urlsplit(full)
    base = up.urlunsplit(('https', HOST, p.path, '', ''))
    if base in url_map:
        return url_map[base], frag, p.query
    if p.path.startswith(('/wp-content/', '/wp-includes/')):
        path = up.unquote(p.path).lstrip('/')
        return (path if path else ''), frag, p.query
    return None


def rewrite_text(text, out_file):
    root_relative = out_file == '404.html'
    keep = {}

    def protect(m):
        k = f'\x00KEEP{len(keep)}\x00'
        keep[k] = m.group(0)
        return k
    text = KEEP_TAG.sub(protect, text)

    def sub(m):
        orig = m.group('url')
        escaped = '\\/' in orig
        r = resolve(orig)
        if r is None:
            return orig
        target, frag, query = r
        if target.endswith('/') or target == '':
            # a directory such as revslider's jsFileLocation
            start = posixpath.dirname(out_file) or '.'
            new = ('/' + target) if root_relative else (posixpath.relpath(target or '.', start) + '/')
        else:
            new = rel(out_file, target, root_relative)
        if query and not target.endswith('__q_'):
            new += '?' + (query.replace('&', '&#038;') if '&#038;' in orig else query)
        if frag:
            new += '#' + frag
        if escaped:
            new = new.replace('/', '\\/')
        return new
    text = URL_RE.sub(sub, text)
    for k, v in keep.items():
        text = text.replace(k, v)
    return text


if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
os.makedirs(DATA, exist_ok=True)
FORCE_HTTPS = 'if (document.location.protocol != "https:") {'
FORCE_HTTPS_LOCAL_OK = ('if (document.location.protocol != "https:" && '
                        '!/^(localhost|127\\.0\\.0\\.1)$/.test(document.location.hostname)) {')
TEXT_EXT = ('.html', '.htm', '.css', '.js', '.json', '.xml', '.svg', '.txt')
for raw_file, out_file in sorted(files.items()):
    src = os.path.join(RAW, raw_file)
    if out_file is None:
        body = json.load(open(src))
        if isinstance(body, dict) and body.get('code'):
            continue  # e.g. an empty extra page of results
        json.dump(body, open(os.path.join(DATA, data_names[raw_file]), 'w'),
                  ensure_ascii=False, indent=1)
        continue
    dst = os.path.join(OUT, out_file)
    os.makedirs(os.path.dirname(dst) or OUT, exist_ok=True)
    if out_file.lower().endswith(('.html', '.htm', '.css')) or out_file == '404.html':
        text = open(src, encoding='utf-8', errors='surrogateescape').read()
        text = rewrite_text(text, out_file)
        # The live site forces https with an inline script. Keep it, but let a
        # local preview (http://localhost / 127.0.0.1) through.
        text = text.replace(FORCE_HTTPS, FORCE_HTTPS_LOCAL_OK)
        open(dst, 'w', encoding='utf-8', errors='surrogateescape').write(text)
    else:
        shutil.copyfile(src, dst)
print('written', sum(1 for v in files.values() if v), 'files to', OUT)
