rwildcard=$(wildcard $1$2) $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2))

RM=rm -f
POSTDIR=posts
SITEDIR=site
POSTEXT=md
COMMIT=

EMPTY :=
BACKSLASH := \$(EMPTY)

ifeq ($(OS),Windows_NT)

copy := copy
backslashize = $(subst /,$(BACKSLASH),$1)

else

copy := cp
backslashize = $1

endif

POSTS=$(call rwildcard,,*.$(POSTEXT))
OUTS=$(POSTS:%.$(POSTEXT)=$(SITEDIR)/%.html)
INDICES=$(POSTS:%index.$(POSTEXT)=%attributes.index)

PNGIN=$(filter-out site/%,$(call rwildcard,,*.png))
PNGS=$(PNGIN:%.png=$(SITEDIR)/%.png)
JPGIN=$(filter-out site/%,$(call rwildcard,,*.jpg))
JPGS=$(JPGIN:%.jpg=$(SITEDIR)/%.jpg)
IMAGEIN=$(PNGIN) $(JPGIN)
IMAGES=$(PNGS) $(JPGS)

build: $(OUTS) $(IMAGES)
.PHONY: build

upload: build
	@git -C site add .
	@git -C site commit -m $(if $(COMMIT),$(COMMIT),"Commit")
	@git -C site push
.PHONY: build

test:
	@echo $(POSTS)
	@echo $(STYLEOUT)
	@echo $(INDICES)
	@echo $(IMAGES)
.PHONY: test

post-index.csv: $(INDICES) merge.py structures.py
	@echo MERGE
	@python merge.py $(INDICES)

%attributes.index: %index.$(POSTEXT) index.py structures.py
	@echo INDEX $<
	@python index.py $< $@

attributes.index: index.$(POSTEXT) index.py structures.py
	@echo INDEX $<
	@python index.py $< $@

$(SITEDIR)/%.html: %.$(POSTEXT) post-index.csv template.html post.py structures.py
	@echo COMPILE $<
	@python post.py $< $@

$(SITEDIR)/%.png: %.png
	@$(copy) $(call backslashize,$<) $(call backslashize,$@)

clean:
	@$(RM) $(INDICES)
