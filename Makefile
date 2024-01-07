rwildcard=$(wildcard $1$2) $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2))

POSTDIR=posts
SITEDIR=site
POSTEXT=md
COMMIT=

POSTS=$(call rwildcard,,*.$(POSTEXT))
OUTS=$(POSTS:%.$(POSTEXT)=$(SITEDIR)/%.html)
INDICES=$(POSTS:%index.$(POSTEXT)=%attributes.index)

build: $(OUTS)
.PHONY: build

upload: build
	@git -C site add .
	@git -C site commit -m $(if $(COMMIT),$(COMMIT),"Commit")
	@git -C site push
.PHONY: build

test:
	@echo $(POSTS)
	@echo $(STYLEOUT)
	@echo $(CFILES)
	@echo $(INDICES)
.PHONY: test

post-index.csv: $(INDICES) merge.py structures.py
	@python merge.py $(INDICES)
	@echo MERGE

%attributes.index: %index.$(POSTEXT) index.py structures.py
	@python index.py $< $@
	@echo INDEX $<

attributes.index: index.$(POSTEXT) index.py structures.py
	@python index.py $< $@
	@echo INDEX $<

$(SITEDIR)/%.html: %.$(POSTEXT) post-index.csv template.html post.py structures.py
	@python post.py $< $@
	@echo COMPILE $<

