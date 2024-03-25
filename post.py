from pathlib import Path
import subprocess as sp
from time import strftime, struct_time
import locale
from typing import Optional
from structures import *

INDEX_FILE = Path('post-index.csv')

def create_post_html_name(year: str, month: str, post_tree: list[tuple[str,str]]) -> str:
	ret = []
	for (name, title) in post_tree:
		ret.append(f'<a href="/posts/{year}/{month}/{name}" class="sidebar-link">&numsp;&numsp;⊡ {title}</a>')
	return '<br/>\n'.join(ret)

MONTH_NAMES = {
	'01': 'Ocak',
	'02': 'Şubat',
	'03': 'Mart',
	'04': 'Nisan',
	'05': 'Mayıs',
	'06': 'Haziran',
	'07': 'Temmuz',
	'08': 'Ağustos',
	'09': 'Eylül',
	'10': 'Ekim',
	'11': 'Kasım',
	'12': 'Aralık',
}

def create_post_html_month(year: str, post_tree: list[tuple[str, list[tuple[str,str]]]], post_time: tuple[str,str]) -> str:
	ret = []
	for (month, tree) in post_tree:
		ret.append(
			f'''
			<details {'open="open"' if post_time[1] == month else ''} class="collapsable-details">
				<summary class="collapsable-summary">{MONTH_NAMES[month]}</summary>
					<sidebar-link-container>
					{create_post_html_name(year, month, tree)}
					</sidebar-link-container>
			</details>
			'''
		)
	return '\n'.join(ret)

def create_post_html_year(post_tree: list[tuple[str, list[tuple[str, list[tuple[str, str]]]]]], post_time: tuple[str,str]) -> str:
	ret = []
	for (year, tree) in post_tree:
		ret.append(
			f'''
			<details {'open="open"' if post_time[0] == year else ''} class="collapsable-details">
				<summary class="collapsable-summary">{year}</summary>
				{create_post_html_month(year, tree, post_time)}
			</details>
			'''
		)
	return '\n'.join(ret)


def get_content(file: Path) -> str:
	pandoc = sp.run(['pandoc', '--mathml', file], capture_output=True)
	content = pandoc.stdout.decode()
	return content

def get_template() -> str:
	template = ""
	with open('template.html', 'r', newline='\n') as f:
		template = f.read()
	return template

def fill_template(template: str, creation_date: str, date: struct_time, content: str, title: str, sidebar: str, tags: TagTree, ourtags: list[str]) -> str:
	datestr = '<div class="time-container"><h3>Gönderi Zamanı:</h3>' + \
		creation_date.replace('\\', '\n') + \
		'</div>'
		# + strftime(r'<div class="time-container"><h3>Değiştirilme Zamanı</h3><p>%Y-%m-%d %H:%M:%S UTC%z</div>', date)
	return template \
			.replace('$#content#$', content) \
			.replace('$#title#$', title) \
			.replace('$#date#$', datestr) \
			.replace('$#posts#$', sidebar) \
			.replace('$#tags#$', tags.html(ourtags)) \
			.replace('$#taglist#$', '<h3>Etiketler:</h3>' + ', \n'.join(map(lambda t: '' + t, sorted(ourtags, key=locale.strxfrm))))

def get_post_time(file: Path) -> Optional[tuple[str,str]]:
	if file.parts[0] != 'posts':
		return None
	return (file.parts[1], file.parts[2])

def do_indexing(args: Arguments) -> tuple[PostIndex, PostAttribute, Optional[tuple[str,str]], tuple[int, struct_time, str]]:
	index = PostIndex(INDEX_FILE)
	post_time = get_post_time(args.file)
	(idx, date, creation_date) = index.date(args.file)
	attributes = PostAttribute(args.file)
	if idx == -1:
		index.append(IndexEntry(str(args.file), creation_date, attributes.title, attributes.tags))
	index.save()
	return index, attributes, post_time, (idx, date, creation_date)

def main(args: Arguments):
	(post_index, post_attributes, post_time, (idx, date, creation_date)) = do_indexing(args)
	post_tree = PostTree(post_index)
	post_sidebar = create_post_html_year(post_tree.tree, post_time or ('',''))
	loc = set_locale()
	tag_tree = TagTree(post_index)
	content = get_content(args.file)
	template = get_template()
	result = fill_template(template, creation_date, date, content, post_attributes.title, post_sidebar, tag_tree, post_attributes.tags)
	
	out = args.outf
	out.parent.mkdir(parents=True, exist_ok=True)

	with open(out, 'w', newline='\n') as f:
		f.write(result)

	set_locale(loc)

if __name__ == '__main__':
	main(Arguments())

