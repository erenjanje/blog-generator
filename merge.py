from structures import PostIndex, set_locale
from argparse import ArgumentParser
from pathlib import Path
from functools import reduce

INDEX_FILE = Path('post-index.csv')

def main():
	loc = set_locale()
	parser = ArgumentParser()
	parser.add_argument('files', nargs='*', type=Path)
	args = parser.parse_args()
	mapping = [(file, PostIndex(file)) for file in args.files]
	mapping.sort(key=lambda m: m[1].index[0].creation_date)
	def accumulator(others: list[str], filename: Path) -> list[str]:
		index: str
		with open(filename, 'r', newline='') as f:
			index = f.read()
		return others + [index]
	merged_index = ''.join(reduce(accumulator, map(lambda m: m[0], mapping), []))
	with open(INDEX_FILE, 'w', newline='') as f:
		f.write(merged_index)
	set_locale(loc)

if __name__ == '__main__':
	main()
