#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from collections.abc import Iterable
from typing import TYPE_CHECKING

import bs4
from pygments import highlight  # pyright: ignore[reportUnknownVariableType]
from pygments.formatters import HtmlFormatter
from pygments.lexers import CLexer

if TYPE_CHECKING:
    from typing_extensions import TypeAlias, TypeGuard

    Tag: TypeAlias = bs4.Tag
    Soup: TypeAlias = bs4.BeautifulSoup

STYLE = 'github-dark'
PARSER = 'html.parser'
FORMATTER: HtmlFormatter[str] = HtmlFormatter(
    encoding='utf-8',
    style=STYLE,
    linenos='table',
)

def gen_css_clases(destination: Path) -> None:
    with open(destination / 'highlights.css', 'w', encoding='utf-8') as css:
        print(FORMATTER.get_style_defs(), file=css)


def add_css(soup: Soup, stylesheet: str) -> Soup:
    head = soup.find('head')
    assert isinstance(head, bs4.Tag)
    head.append(soup.new_tag('link', rel='stylesheet', type='text/css', href=stylesheet))
    return soup


def highlight_codeblocks(soup: Soup) -> Soup:
    lexer = CLexer()
    for pre_tag in soup.find_all('pre', class_='example-preformatted'):
        assert isinstance(pre_tag, bs4.Tag)
        div = bs4.BeautifulSoup(highlight(pre_tag.get_text(), lexer, FORMATTER), PARSER)
        assert div.table is not None
        pre_tag.replace_with(div.table)
    return soup


def is_tag_list(obj: Iterable[object]) -> TypeGuard[list[bs4.Tag]]:
    return isinstance(obj, list) and all(isinstance(i, bs4.Tag) for i in obj)


def generate_navbar(soup: Soup) -> Soup:
    navs = soup.find_all('div', class_='nav-panel')

    if not navs:
        return soup
    assert len(navs) <= 2, 'Found more than 2 navbars'
    assert is_tag_list(navs), navs

    top_nav = navs[0]
    top_nav.name = 'nav'
    index_div = soup.new_tag('div', attrs={'class': 'nav-index'})
    topics_div = soup.new_tag('div', attrs={'class': 'nav-topics'})
    empty_div = soup.new_tag('div', attrs={'class': 'empty'})
    top_nav.append(index_div)
    top_nav.append(topics_div)

    index_types = ['contents', 'index']
    topics_types = ['prev', 'up', 'next']
    index_tags = [copy.copy(empty_div) for _ in index_types]
    topic_tags = [copy.copy(empty_div) for _ in topics_types]
    assert top_nav.p is not None

    for child in top_nav.p.children:
        if not (isinstance(child, bs4.Tag) and child.name == 'a'):
            continue
        rel = child['rel'][0]
        if rel in topics_types:
            topic_tags[topics_types.index(rel)] = child
        elif rel in index_types:
            index_tags[index_types.index(rel)] = child
    for tag in index_tags:
        index_div.append(tag.extract())
    for tag in topic_tags:
        topics_div.append(tag.extract())
    top_nav.p.decompose()

    if len(navs) != 2:
        return soup
    # Modified the copy before replacing bottom_nav or the changes won't take effect
    tmp_nav = copy.copy(top_nav)
    for a in tmp_nav.find_all('a'):
        assert isinstance(a, bs4.Tag)
        del a['rel']
        del a['accesskey']
    assert tmp_nav.div is not None
    tmp_nav.append(tmp_nav.div.extract())  # swap div order
    navs[1].replace_with(tmp_nav)  # bottom nav

    return soup


def process_html(html_source: Path, stylesheet: Path, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    html_pages = tuple(html_source.glob('*.html'))
    total = len(html_pages)
    pad = len(str(total))

    for i, file in enumerate(html_pages, 1):
        print(f'[{i:>{pad}} - {total}]', file.name)
        if not file.is_file():
            continue
        process_html_page(file, stylesheet, destination)


def process_html_page(html_source: Path, stylesheet: Path, destination: Path):
    with open(html_source, 'r', encoding='utf-8') as f:
        html = bs4.BeautifulSoup(f, PARSER)
    add_css(html, stylesheet.name)
    highlight_codeblocks(html)
    generate_navbar(html)
    with open(destination / html_source.name, 'w', encoding='utf-8') as out:
        out.write(html.decode(formatter='html'))


def gen_symbolic_links(destination: Path, *paths: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in paths:
        link = destination / path.name
        if not link.exists():
            link.symlink_to(path.resolve())


def main() -> int:
    parser = argparse.ArgumentParser(description='beautify the GNU C Manual')
    parser.add_argument('--css', action='store_true')
    parser.add_argument('--html', action='store_true')
    parser.add_argument('--html-page')
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.error('Choose at least one option')

    destination = Path('docs/')
    source = Path('gnu-c-manual/c.html.d/')
    css_dir = Path('css/')
    css = css_dir / 'styles.css'

    if args.css:
        gen_css_clases(css_dir)
    if args.html:
        if not source.exists():
            parser.error(f"'{source}' doesn't exist, generate the HTML files first")
        process_html(source, css, destination)
        print((destination / 'index.html').resolve().as_uri())
    if args.html_page:
        html_page = Path(args.html_page)
        if not html_page.exists():
            parser.error(f"'{html_page}' doesn't exists")
        process_html_page(html_page, css, destination)
    if args.html_page or args.html:
        gen_symbolic_links(destination, css)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
