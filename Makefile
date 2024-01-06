rwildcard=$(wildcard $1$2) $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2))

POSTDIR=posts
SITEDIR=site
POSTEXT=md
TITLE=
COMMIT=

POSTS=$(call rwildcard,,*.$(POSTEXT))
OUTS=$(POSTS:%.$(POSTEXT)=$(SITEDIR)/%.html)

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
.PHONY: test

$(SITEDIR)/%.html: template.html post.py %.$(POSTEXT) post-index.csv
	@echo COMPILE $(word 3, $^)
	python post.py $(if $(TITLE),--title $(TITLE),) $(word 3, $^) $@

