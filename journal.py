"""Build a small static journal from content/*/index.md."""
import argparse
import datetime as dt
import functools
import html
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit

import markdown
import yaml

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif'}
escape = lambda value: html.escape(str(value), quote=True)


def entries():
    result = []
    for path in (ROOT / 'content').glob('*/index.md'):
        text = path.read_text(encoding='utf-8-sig')
        match = re.match(r'\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)', text, re.S)
        if not match:
            raise ValueError(f'{path}: 需要以 --- 包围的文章信息')
        meta = yaml.safe_load(match.group(1)) or {}
        if not isinstance(meta, dict):
            raise ValueError(f'{path}: 文章信息必须是键值对')
        if meta.get('draft', False):
            continue
        slug = path.parent.name
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError(f'{path}: 文件夹名只能用小写字母、数字和连字符')
        try:
            date = dt.date.fromisoformat(str(meta['date']))
        except (KeyError, ValueError) as error:
            raise ValueError(f'{path}: date 应为 YYYY-MM-DD') from error
        result.append({'slug': slug, 'date': date, 'title': str(meta.get('title') or ''),
                       'body': match.group(2).strip(), 'folder': path.parent})
    return sorted(result, key=lambda item: (item['date'], item['slug']), reverse=True)


def excerpt(body):
    if '<!-- more -->' in body:
        return body.split('<!-- more -->', 1)[0], True
    blocks = re.split(r'\n\s*\n', body)
    if len(body) <= 600 or len(blocks) < 2:
        return body, False
    selected = []
    for block in blocks:
        selected.append(block)
        if len('\n\n'.join(selected)) >= 600:
            break
    return '\n\n'.join(selected), len(selected) < len(blocks)


def render_body(text, entry, prefix):
    text = text.replace('<!-- more -->', '')
    rendered = markdown.markdown(text, extensions=['extra', 'sane_lists'])

    def fix_url(match):
        attribute, value = match.group(1), html.unescape(match.group(2))
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or value.startswith(('/', '#')):
            return match.group(0)
        local_path = unquote(parsed.path)
        parts = Path(local_path).parts
        if not local_path or '..' in parts or '\\' in local_path:
            raise ValueError(f'{entry["slug"]}: 不支持的相对路径 {value}')
        asset = entry['folder'] / local_path
        if not asset.is_file() or asset.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f'{entry["slug"]}: 找不到图片或格式不支持：{value}')
        if asset.is_symlink() or not asset.resolve().is_relative_to(entry['folder'].resolve()):
            raise ValueError(f'{entry["slug"]}: 不支持指向文件夹外的图片')
        url = prefix + quote(local_path, safe='/')
        if parsed.query:
            url += '?' + parsed.query
        if parsed.fragment:
            url += '#' + parsed.fragment
        return f'{attribute}="{escape(url)}"'
    return re.sub(r'(src|href)="([^"]+)"', fix_url, rendered)


def layout(content, root, title='', article=False):
    head_title = f'{title} · YanrhArcheive' if title else 'YanrhArcheive'
    top = (f'<a class="back" href="{root}">← 返回 / Back</a>' if article else
           '<div class="masthead"><p class="eyebrow">A PERSONAL ARCHIVE</p><h1>YanrhArcheive</h1></div>')
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
<title>{escape(head_title)}</title><script src="{root}reading.js"></script><link rel="stylesheet" href="{root}style.css"></head>
<body><a class="skip" href="#writing">跳至正文</a><div class="shell"><header class="topbar"><a class="wordmark" href="{root}" aria-label="YanrhArcheive 首页">YA<span>.</span></a><button class="theme-toggle" type="button" aria-label="切换明暗主题" title="切换明暗主题" hidden>☾</button></header>
{top}<main id="writing">{content}</main><footer><span>YanrhArcheive</span><a href="#" aria-label="返回顶部">↑</a></footer></div></body></html>'''


def card(entry, full=False):
    path = '' if full else f'entries/{entry["slug"]}/'
    link = './' if full else path
    body, more = (entry['body'], False) if full else excerpt(entry['body'])
    tag = 'h1' if full else 'h2'
    heading = f'<{tag}>{escape(entry["title"])}</{tag}>' if full and entry['title'] else (
        f'<{tag}><a href="{link}">{escape(entry["title"])}</a></{tag}>' if entry['title'] else '')
    date = entry['date'].isoformat()
    continue_link = f'<a class="continue" href="{link}">继续阅读 <span aria-hidden="true">↗</span></a>' if more else ''
    return f'''<article class="entry"><div class="entry-date"><a href="{link}"><time datetime="{date}">{date}</time></a></div>{heading}<div class="prose">{render_body(body, entry, path)}</div>{continue_link}</article>'''


def build():
    posts = entries()
    if OUT.is_symlink() or OUT.resolve() != ROOT.resolve() / 'dist':
        raise ValueError('不安全的输出目录')
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for asset in ('style.css', 'reading.js'):
        shutil.copy2(ROOT / asset, OUT / asset)
    # Crawlers must be able to request HTML pages to see their noindex meta tag.
    (OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\n', encoding='utf-8')
    for entry in posts:
        dest = OUT / 'entries' / entry['slug']
        dest.mkdir(parents=True)
        for asset in entry['folder'].rglob('*'):
            if asset.is_file() and asset.suffix.lower() in IMAGE_EXTENSIONS:
                if asset.is_symlink() or not asset.resolve().is_relative_to(entry['folder'].resolve()):
                    raise ValueError(f'不支持指向文件夹外的图片：{asset}')
                target = dest / asset.relative_to(entry['folder'])
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, target)
        (dest / 'index.html').write_text(layout(card(entry, True), '../../', entry['title'] or str(entry['date']), True), encoding='utf-8')
    controls = '<div class="section-heading"><span>WRITING</span><button class="sort-toggle" type="button" aria-label="按时间正序排列" hidden>时间 ↓</button></div>'
    feed = controls + '<div id="entries">' + ''.join(card(entry) for entry in posts) + '</div>'
    if not posts:
        feed += '<p class="empty">这里还没有文章。</p>'
    (OUT / 'index.html').write_text(layout(feed, './'), encoding='utf-8')
    print(f'Built {len(posts)} entries in {OUT}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['build', 'preview'])
    parser.add_argument('--port', type=int, default=4173)
    args = parser.parse_args()
    build()
    if args.command == 'preview':
        print(f'Preview: http://127.0.0.1:{args.port}', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port), functools.partial(SimpleHTTPRequestHandler, directory=str(OUT))).serve_forever()

