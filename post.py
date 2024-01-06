from argparse import ArgumentParser
from pathlib import Path
import subprocess as sp
from os import remove
from shutil import copyfile
from os import path
from time import localtime, strftime, struct_time
import locale
import csv
from typing import Optional, cast, NamedTuple

INDEX_FILE = Path('post-index.csv')

class PostAttribute:
    __slots__ = ('title', 'tags')
    def __init__(self, file: Path):
        file_attributes = ''
        with open(file, 'r', newline='\n') as f:
            file_attributes = f.readline()
        file_attributes = list(map(lambda s: s.strip(), file_attributes[5:-5].split(';')))
        self.title: Optional[str] = file_attributes[0] if len(file_attributes) > 0 else None
        self.tags: Optional[list[str]] = list(map(lambda s: s.strip(), file_attributes[1].split(','))) if len(file_attributes) > 1 else None
    def __repr__(self) -> str:
        return f'PostAttribute(title={repr(self.title)}, tags={repr(self.tags)})'

class IndexEntry(NamedTuple):
    file: str
    creation_date: str
    title: str
    tags: list[str]

class PostIndex:
    __slots__ = ('index', 'file')
    def __init__(self, index_file: Path):
        index: list[IndexEntry]
        with open(index_file, 'r', newline='') as f:
            reader = csv.reader(f)
            index = cast(list[IndexEntry], list(map(lambda t: IndexEntry(t[0], t[1], t[2], t[3].split(',')), reader)))
        self.index = index
        self.file = index_file
    def find(self, file: Path) -> int:
        file_str = str(file)
        for (i,entry) in enumerate(self.index):
            if entry[0] == file_str:
                return i
        return -1
    def append(self, entry: IndexEntry):
        self.index.append(entry)
        self.index.sort(key=lambda t: t[1])
    def save(self):
        with open(self.file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(map(lambda e: (e.file, e.creation_date, e.title, ','.join(e.tags)), self.index))
    def __getitem__(self, index: int) -> IndexEntry:
        return self.index[index]
    def date(self, file: Path) -> tuple[int,struct_time,str]:
        date = localtime(path.getmtime(file))
        idx = self.find(file)
        creation_date = (self.index[idx][1] if idx != -1 else strftime('%Y-%m-%d\\%H:%M:%S\\UTC%z', date))
        return (idx, date, creation_date)
    
class PostTree:
    __slots__ = ('tree')
    def __init__(self, index: PostIndex):
        def create_post_list(index: list[IndexEntry]) -> list[tuple[str,str,str,str]]:
            ret = []
            for (filename_, _, title, _) in index:
                filename = Path(filename_)
                parts = filename.parts
                if parts[0] == 'posts' and len(parts) == 5:
                    parts = parts[1:-1]
                    parts = (*parts, title)
                    ret.append(parts)
            return ret
        post_list = create_post_list(index.index)
        ret = []
        def find(array, query):
            for (i, (key, _)) in enumerate(array):
                if key == query:
                    return i
            return -1
        for (year, month, name, title) in post_list:
            year_index = find(ret, year)
            if year_index == -1:
                ret.append((year, []))
                year_index = len(ret)-1
            month_index = find(ret[year_index][1], month)
            if month_index == -1:
                ret[year_index][1].append((month, []))
                month_index = len(ret[year_index][1])-1
            ret[year_index][1][month_index][1].append((name, title))
        self.tree = ret

def create_post_html_name(year: str, month: str, post_tree: list[tuple[str,str]]) -> str:
    ret = []
    for (name, title) in post_tree:
        ret.append(f'<a href="/posts/{year}/{month}/{name}" class="sidebar-link">{title}</a>')
    return '<br/>\n'.join(ret)

def create_post_html_month(year: str, post_tree: list[tuple[str, list[tuple[str,str]]]]) -> str:
    ret = []
    for (month, tree) in post_tree:
        ret.append(
            f'''
            <details>
                <summary>{month}</summary>
                {create_post_html_name(year, month, tree)}
            </details>
            '''
        )
    return '\n'.join(ret)

def create_post_html_year(post_tree: list[tuple[str, list[tuple[str, list[tuple[str, str]]]]]]) -> str:
    ret = []
    for (year, tree) in post_tree:
        ret.append(
            f'''
            <details>
                <summary>{year}</summary>
                {create_post_html_month(year, tree)}
            </details>
            '''
        )
    return '\n'.join(ret)

def create_post_tag(tag) -> str:
    return f'<details><summary><a href="/{tag}" class="sidebar-link">{tag}<a/></summary></details>'

def get_arguments():
    parser = ArgumentParser()
    parser.add_argument('file', type=Path)
    parser.add_argument('outf', type=Path)
    args = parser.parse_args()
    return args

def set_locale(new_loc = None):
    loc = locale.getlocale()
    locale.setlocale(locale.LC_ALL, 'tr_TR' if new_loc is None else new_loc)
    return loc


def get_content(file: Path) -> str:
    pandoc = sp.run(['pandoc', file], capture_output=True)
    content = pandoc.stdout.decode()
    return content

def get_template() -> str:
    template = ""
    with open('template.html', 'r', newline='\n') as f:
        template = f.read()
    return template

def fill_template(template: str, creation_date: str, date: struct_time, content: str, title: Optional[str], sidebar: str, tags: list[str]) -> str:
    datestr = '<p>Oluşturulma Zamanı<br/>' + \
        creation_date.replace('\\', '<br/>') + \
        '</p>' + \
        strftime(r'<p>Değiştirilme Zamanı<br/>%Y-%m-%d<br/>%H:%M:%S<br/>UTC%z</p>', date)
    return template \
            .replace('$#content#$', content) \
            .replace('$#title#$', title or '') \
            .replace('$#date#$', datestr) \
            .replace('$#posts#$', sidebar) \
            .replace('$#tags#$', '\n'.join(map(create_post_tag, tags)))

def main():
    post_index = PostIndex(INDEX_FILE)
    post_tree = PostTree(post_index)
    post_sidebar = create_post_html_year(post_tree.tree)
    args = get_arguments()
    loc = set_locale()
    post_attributes = PostAttribute(args.file)
    (index_index, date, creation_date) = post_index.date(args.file)
    content = get_content(args.file)
    template = get_template()
    result = fill_template(template, creation_date, date, content, post_attributes.title, post_sidebar, post_attributes.tags or [])

    if index_index == -1:
        post_index.append(IndexEntry(str(args.file), creation_date, post_attributes.title or '', post_attributes.tags or []))
        post_index.save()
    
    out = args.outf
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, 'w', newline='\n') as f:
        f.write(result)

    set_locale(loc)

if __name__ == '__main__':
    main()

