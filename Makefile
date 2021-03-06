SOURCES := $(wildcard src/*.py) src/shebang \
           src/interactive_command_list_start src/interactive_command_list_end
GENERATED := src/interactive_command_list_middle \
             src/InteractiveModeCommandList.py
ZIPSOURCES := $(wildcard src/*.py) src/InteractiveModeCommandList.py
BINARY := e2x.py
LICENSE := LICENSE.txt
VERSION := $(shell sed -n "s/^progver = '\([^']*\)'$$/\1/p" src/cli.py)
DIST := $(patsubst %.py,%-$(VERSION)-src.zip,$(BINARY))
BINDIST := $(patsubst %-src.zip,%-bin.zip,$(DIST))
PREVIEW := $(patsubst %.py,%-preview.zip,$(BINARY))
ZIP := $(patsubst %.py,%.zip,$(BINARY))
TESTS := $(wildcard tests/*_test.py tests/scripttest/*.py) \
         tests/interactive_statements
RUNTESTS := tests/run_tests.sh
RUNTESTS_WIN := tests/run_tests.bat
PYTHON := python3
INTEGRATIONTEST := tests/IntegrationTest.py
MARKDOWNDOCS := README.md $(wildcard docs/*.md)
HTMLDOCS := $(patsubst %.md,%.html,$(MARKDOWNDOCS))
TEMPLATES := $(wildcard templates/*)
TOOLS := $(wildcard tools/*)

all: $(BINARY) html

$(BINARY): $(GENERATED) $(ZIP) src/shebang
	cat src/shebang $(ZIP) > $@
	chmod +x $@

$(ZIP): $(SOURCES) $(GENERATED) Makefile
	zip -j $@ $(ZIPSOURCES)

src/interactive_command_list_middle: Makefile docs/ReleaseNotes.md
	sed '1,/## Function Module Interactive/d;/^## .*$$/d' \
		docs/ReleaseNotes.md | \
		sed '1,/### Commands/d;s/^ *//;/^ *$$/d' > $@

src/InteractiveModeCommandList.py: Makefile src/interactive_command_list_middle
	cat src/interactive_command_list_start \
		src/interactive_command_list_middle \
		src/interactive_command_list_end > $@

src-dist: distclean $(DIST)

$(DIST): $(SOURCES) $(TESTS) $(RUNTESTS) $(RUNTESTS_WIN) \
            $(INTEGRATIONTEST) $(MARKDOWNDOCS) $(LICENSE) $(TEMPLATES) \
            $(TOOLS) Makefile
	$(RM) $@
	zip $@ $(SOURCES) $(TESTS) $(RUNTESTS) $(RUNTESTS_WIN) \
               $(INTEGRATIONTEST) $(MARKDOWNDOCS) $(LICENSE) $(TEMPLATES) \
               $(TOOLS) Makefile

bin-dist: distclean $(BINDIST)

$(BINDIST): $(BINARY) $(MARKDOWNDOCS) $(LICENSE)
	$(RM) $@
	zip $@ $(BINARY) $(MARKDOWNDOCS) $(LICENSE)

preview: $(PREVIEW)

$(PREVIEW): $(BINARY) $(SOURCES) $(TESTS) $(RUNTESTS) $(RUNTESTS_WIN) \
            $(INTEGRATIONTEST) $(MARKDOWNDOCS) $(LICENSE)
	$(RM) $@
	zip $@ $(BINARY) $(SOURCES) $(TESTS) $(RUNTESTS) $(RUNTESTS_WIN) \
               $(INTEGRATIONTEST) $(MARKDOWNDOCS) $(LICENSE)

check: $(BINARY)
	-$(RUNTESTS)
	@echo
	$(PYTHON) $(INTEGRATIONTEST) $(BINARY)

%.html : %.md Makefile
	sed 's/\.md)/.html)/g' $< | pandoc -f markdown -t html -o $@

html: $(HTMLDOCS) Makefile

clean:
	$(RM) -r $(BINARY) $(PREVIEW) $(HTMLDOCS) $(GENERATED)

distclean: clean
	$(RM) -r __pycache__ src/__pycache__ tests/scripttest/__pycache__ \
		$(wildcard src/*.pyc) $(GENERATED)

.PHONY: clean distclean check
.INTERMEDIATE: $(ZIP)
