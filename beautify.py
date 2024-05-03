#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
import re
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import bs4
from pygments import highlight  # pyright: ignore[reportUnknownVariableType]
from pygments.formatters import HtmlFormatter
from pygments.lexers import CLexer

if TYPE_CHECKING:
    from typing_extensions import TypeAlias, TypeGuard

    Tag: TypeAlias = bs4.Tag
    Soup: TypeAlias = bs4.BeautifulSoup


CLASS_EXTEN_LEVEL_PATTERN = re.compile(r'\w+-level-extent')
STYLE = 'github-dark'
PARSER = 'html.parser'
FORMATTER: HtmlFormatter[str] = HtmlFormatter(
    encoding='utf-8',
    style=STYLE,
    linenos='table',
)


class Assets(NamedTuple):
    prev_img: Path
    next_img: Path


def gen_css_clases(destination: Path) -> None:
    with open(destination / 'highlights.css', 'w', encoding='utf-8') as css:
        print(FORMATTER.get_style_defs(), file=css)


def add_css(soup: Soup, stylesheet: Path) -> Soup:
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


def is_tag_list(obj: Iterable[object]) -> TypeGuard[list[Tag]]:
    return isinstance(obj, list) and all(isinstance(i, bs4.Tag) for i in obj)


def generate_navbar(soup: Soup, assets: Assets) -> Soup:
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

    index_rel = ['contents', 'index']
    topic_rel = ['prev', 'up', 'next']
    index_tags = [copy.copy(empty_div) for _ in index_rel]
    topic_tags = [copy.copy(empty_div) for _ in topic_rel]
    assert top_nav.p is not None

    for child in top_nav.p.children:
        if not (isinstance(child, bs4.Tag) and child.name == 'a'):
            continue
        rel = child['rel'][0]
        if rel in topic_rel:
            topic_tags[topic_rel.index(rel)] = child.extract()
        elif rel in index_rel:
            index_tags[index_rel.index(rel)] = child.extract()
    top_nav.p.decompose()

    for tag in index_tags:
        index_div.append(tag)
    for tag in topic_tags:
        if tag.contents:
            span = soup.new_tag('span')
            span.string = tag.get_text()
            tag.clear()
            rel = tag['rel'][0]
            if rel == topic_rel[0]:
                tag.append(soup.new_tag('img', src=assets.prev_img))
                tag.append(span)
            elif rel == topic_rel[1]:
                tag.append(span)
            elif rel == topic_rel[2]:
                tag.append(span)
                tag.append(soup.new_tag('img', src=assets.next_img))
        topics_div.append(tag)

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


# toc -> table of contents
def change_mini_toc(soup: Soup) -> Soup:
    toc = soup.find('ul', class_='mini-toc')
    if not isinstance(toc, bs4.Tag):
        return soup

    toc.name = 'ol'
    extent_tag = soup.find(class_=CLASS_EXTEN_LEVEL_PATTERN)
    if not isinstance(extent_tag, bs4.Tag):
        return soup

    extent_level = extent_tag['class'][0].split('-')[0]
    toc_header = soup.new_tag('span', attrs={'class': 'mini-content-header'})
    toc_header.string = f'{extent_level.title()} Content'

    extent_header = soup.find(class_=extent_level)
    assert isinstance(extent_header, bs4.Tag)  # This should exists and be a tag

    div = soup.new_tag('div', attrs={'class': 'mini-content'})
    div.append(toc_header)
    div.append(toc.extract())
    extent_header.insert_after(div)
    assert div.parent
    # the mini-toc may overflow
    div.parent['class'].append('contain-float')  # pyright: ignore[reportAttributeAccessIssue]
    return soup


def process_html(destination: Path, html_source: Path, stylesheet: Path, assets: Assets) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    html_pages = tuple(html_source.glob('*.html'))
    total = len(html_pages)
    pad = len(str(total))

    for i, file in enumerate(html_pages, 1):
        print(f'[{i:>{pad}} - {total}]', file.name)
        if not file.is_file():
            continue
        process_html_page(destination, file, stylesheet, assets)


def process_html_page(
    destination: Path, html_source: Path, stylesheet: Path, assets: Assets
) -> None:
    with open(html_source, 'r', encoding='utf-8') as f:
        html = bs4.BeautifulSoup(f, PARSER)
    add_css(html, stylesheet)
    highlight_codeblocks(html)
    generate_navbar(html, assets)
    change_mini_toc(html)
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
    parser.add_argument('--symlink', action='store_true')
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.error('Choose at least one option')

    destination = Path('docs/')
    source = Path('gnu-c-manual/c.html.d/')
    css_dir = Path('css/')
    css = css_dir / 'styles.css'
    assets_dir = Path('assets/')
    assets = Assets(
        prev_img=assets_dir / 'go-previous.svg',
        next_img=assets_dir / 'go-next.svg',
    )

    if args.css:
        gen_css_clases(css_dir)
    if args.html:
        if not source.exists():
            parser.error(f"'{source}' doesn't exist, generate the HTML files first")
        process_html(destination, source, css, assets)
        print((destination / 'index.html').resolve().as_uri())
    if args.html_page:
        html_page = Path(args.html_page)
        if not html_page.exists():
            parser.error(f"'{html_page}' doesn't exists")
        process_html_page(destination, html_page, css, assets)
    if args.symlink or args.html_page or args.html:
        gen_symbolic_links(destination, css_dir, assets_dir)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
