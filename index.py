from structures import *

INDEX_FILE = Path("post-index.csv")

def index(args: Arguments):
	index = PostIndex(args.outf)
	attributes = PostAttribute(args.file)
	idx = index.find(args.file)
	changed: bool
	index[idx].title = attributes.title
	index[idx].tags = attributes.tags
	if idx == -1:
		index.append(
			IndexEntry(
				str(args.file),
				strftime(
					"%Y-%m-%d\\%H:%M:%S\\UTC%z", localtime(path.getmtime(args.file))
				),
				attributes.title,
				sorted(attributes.tags, key=locale.strxfrm),
			)
		)
		changed = True
	else:
		changed = (index[idx].title != attributes.title) or (
			index[idx].tags != attributes.tags
		)
	if changed:
		index.save()


if __name__ == "__main__":
	index(Arguments())
