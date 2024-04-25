#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

import bs4
from pygments import highlight  # pyright: ignore[reportUnknownVariableType]
from pygments.formatters import HtmlFormatter
from pygments.lexers import CLexer

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    Soup: TypeAlias = bs4.BeautifulSoup

PARSER = 'html.parser'
CODE_CLASS = 'example-preformatted'


def gen_css_clases(destination: Path) -> None:
    with open(destination / 'highlights.css', 'w', encoding='utf-8') as css:
        css.write(HtmlFormatter().get_style_defs(f'pre.{CODE_CLASS}'))


def add_css(soup: Soup, stylesheet: str) -> Soup:
    head = soup.find('head')
    assert isinstance(head, bs4.Tag)
    head.append(soup.new_tag('link', rel='stylesheet', type='text/css', href=stylesheet))
    return soup


def highlight_codeblocks(soup: Soup) -> Soup:
    formatter: HtmlFormatter[str] = HtmlFormatter(encoding='utf-8')
    lexer = CLexer()
    for pre_tag in soup.find_all('pre', class_=CODE_CLASS): # pyright: ignore
        assert isinstance(pre_tag, bs4.Tag)
        div = bs4.BeautifulSoup(highlight(pre_tag.get_text(), lexer, formatter), PARSER)
        assert div.pre is not None
        div.pre['class'] = CODE_CLASS
        pre_tag.replace_with(div.pre)
    return soup


def process_html(html_source: Path, stylesheet: Path, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    dest_css = destination / stylesheet.name

    if not dest_css.exists():
        dest_css.symlink_to(stylesheet.absolute())

    for file in html_source.glob('*.html'):
        print('Processing:', file)
        if not file.is_file():
            continue
        with open(file, 'r', encoding='utf-8') as f:
            html = bs4.BeautifulSoup(f, PARSER)
        add_css(html, stylesheet.name)
        highlight_codeblocks(html)
        with open(destination / file.name, 'w', encoding='utf-8') as out:
            out.write(html.decode(formatter='html'))


def main() -> int:
    parser = argparse.ArgumentParser(description='beautify the GNU C Manual')
    parser.add_argument('--html', action='store_true')
    parser.add_argument('--css', action='store_true')
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.error('Choose at least one option')

    destination = Path('docs/')
    source = Path('gnu-c-manual/c.html.d/')
    css_dir = Path('css/')

    if args.css:
        gen_css_clases(css_dir)
    if args.html:
        if not source.exists():
            print(f"'{source}' doesn't exist, generate the HTML files first")
            return 1
        process_html(source, css_dir / 'styles.css', destination)
        print((destination / 'index.html').resolve().as_uri())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
