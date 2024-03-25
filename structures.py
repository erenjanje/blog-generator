from pathlib import Path
from typing import Optional, cast
import csv
from time import localtime, struct_time, strftime
from os import path
from argparse import ArgumentParser
import locale


class PostAttribute:
    __slots__ = ("title", "tags")

    def __init__(self, file: Path):
        file_attributes = ""
        with open(file, "r", newline="\n") as f:
            file_attributes = f.readline()
        file_attributes = list(
            map(lambda s: s.strip(), file_attributes.strip()[4:-3].strip().split(";"))
        )
        self.title: str = file_attributes[0] if len(file_attributes) > 0 else ""
        self.tags: list[str] = (
            list(map(lambda s: s.strip(), file_attributes[1].split(",")))
            if len(file_attributes) > 1
            else []
        )

    def __repr__(self) -> str:
        return f"PostAttribute(title={repr(self.title)}, tags={repr(self.tags)})"


class IndexEntry:
    __slots__ = ("file", "creation_date", "title", "tags")

    def __init__(self, file: str, creation_date: str, title: str, tags: list[str]):
        if tags == [""]:
            tags = []
        self.file = file
        self.creation_date = creation_date
        self.title = title
        self.tags = tags

    def get(self) -> tuple[str, str, str, list[str]]:
        return (self.file, self.creation_date, self.title, self.tags)

    def __repr__(self) -> str:
        return f"IndexEntry(file={repr(self.file)}, creation_date={repr(self.creation_date)}, title={repr(self.title)}, tags={repr(self.tags)})"


class PostIndex:
    __slots__ = ("index", "file")

    def __init__(self, index_file: Path):
        index: list[IndexEntry]
        index_file.touch()
        with open(index_file, "r", newline="") as f:
            reader = csv.reader(f)
            index = cast(
                list[IndexEntry],
                list(
                    map(lambda t: IndexEntry(t[0], t[1], t[2], t[3].split(",")), reader)
                ),
            )
        self.index = index
        self.file = index_file

    def find(self, file: Path) -> int:
        file_str = str(file)
        for i, entry in enumerate(self.index):
            if entry.file == file_str:
                return i
        return -1

    def append(self, entry: IndexEntry):
        self.index.append(entry)
        self.index.sort(key=lambda t: t.creation_date)

    def save(self):
        with open(self.file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(
                map(
                    lambda e: (e.file, e.creation_date, e.title, ",".join(e.tags)),
                    self.index,
                )
            )

    def __getitem__(self, index: int) -> IndexEntry:
        return self.index[index]

    def date(self, file: Path) -> tuple[int, struct_time, str]:
        date = localtime(path.getmtime(file))
        idx = self.find(file)
        creation_date = (
            self.index[idx].creation_date
            if idx != -1
            else strftime("%Y-%m-%d\\%H:%M:%S\\UTC%z", date)
        )
        return (idx, date, creation_date)

    def __repr__(self) -> str:
        return f"PostIndex(index={repr(self.index)}, file={repr(self.file)})"


class PostTree:
    __slots__ = "tree"

    def __init__(self, index: PostIndex):
        def create_post_list(
            index: list[IndexEntry],
        ) -> list[tuple[str, str, str, str]]:
            ret = []
            for filename_, _, title, _ in map(lambda i: i.get(), index):
                filename = Path(filename_)
                parts = filename.parts
                if parts[0] == "posts" and len(parts) == 5:
                    parts = parts[1:-1]
                    parts = (*parts, title)
                    ret.append(parts)
            return ret

        post_list = create_post_list(index.index)
        ret = []

        def find(array, query):
            for i, (key, _) in enumerate(array):
                if key == query:
                    return i
            return -1

        for year, month, name, title in post_list:
            year_index = find(ret, year)
            if year_index == -1:
                ret.append((year, []))
                year_index = len(ret) - 1
            month_index = find(ret[year_index][1], month)
            if month_index == -1:
                ret[year_index][1].append((month, []))
                month_index = len(ret[year_index][1]) - 1
            ret[year_index][1][month_index][1].append((name, title))
        self.tree = ret


class TagTree:
    __slots__ = "tree"

    def __init__(self, index: PostIndex):
        self.tree: dict[str, list[tuple[str, str]]] = {}
        for file, _, title, tags in map(lambda e: e.get(), index.index):
            for tag in tags:
                self.tree.setdefault(tag, []).append((file, title))

    def __repr__(self) -> str:
        return f"TagTree(tree={repr(self.tree)})"

    def html(self, ourtags: list[str]) -> str:
        current_tags: set[str] = set(ourtags)
        tags = list(filter(lambda t: t != "", self.tree.keys()))
        tags.sort(key=locale.strxfrm)
        ret = []
        for tag in tags:
            ret.append(
                f"""<details class="collapsable-details">
                     <summary class="{"current-tag" if tag in current_tags else ""} collapsable-summary">
                            {tag} ({len(self.tree[tag])})
                     </summary>
                  <sidebar-link-container>"""
            )
            for file, title in self.tree[tag]:
                ret.append(
                    f"""<a href="/{'/'.join(Path(file).parts[:-1])}" class="sidebar-link">&numsp;&numsp;⊡ {title}</a>"""
                )
            ret.append("</sidebar-link-container></details>\n")
        return "".join(ret)


class Arguments:
    __slots__ = ("file", "outf")

    def __init__(self):
        parser = ArgumentParser()
        parser.add_argument("file", type=Path)
        parser.add_argument("outf", type=Path)
        args = parser.parse_args()
        self.file: Path = args.file
        self.outf: Path = args.outf


def set_locale(new_loc=None):
    loc = locale.getlocale()
    locale.setlocale(locale.LC_ALL, "tr_TR.utf8" if new_loc is None else new_loc)
    return loc
