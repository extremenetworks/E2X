SOURCES := $(wildcard src/*.py) src/shebang
BINARY := e2x.py
LICENSE := LICENSE.txt
VERSION := $(shell sed -n "s/^progver = '\([^']*\)'$$/\1/p" src/cli.py)
DIST := $(patsubst %.py,%-$(VERSION)-src.zip,$(BINARY))
BINDIST := $(patsubst %-src.zip,%-bin.zip,$(DIST))
PREVIEW := $(patsubst %.py,%-preview.zip,$(BINARY))
ZIP := $(patsubst %.py,%.zip,$(BINARY))
TESTS := $(wildcard tests/*_test.py tests/scripttest/*.py)
RUNTESTS := tests/run_tests.sh
RUNTESTS_WIN := tests/run_tests.bat
PYTHON := python3
INTEGRATIONTEST := tests/IntegrationTest.py
MARKDOWNDOCS := README.md $(wildcard docs/*.md)
HTMLDOCS := $(patsubst %.md,%.html,$(MARKDOWNDOCS))
TEMPLATES := $(wildcard templates/*)
TOOLS := $(wildcard tools/*)

all: $(BINARY)

$(BINARY): $(ZIP) src/shebang
	cat src/shebang $(ZIP) > $@
	chmod +x $@

$(ZIP): $(SOURCES) Makefile
	zip -j $@ $(SOURCES)

src-dist: $(DIST)

$(DIST): $(SOURCES) $(TESTS) $(RUNTESTS) $(RUNTESTS_WIN) \
            $(INTEGRATIONTEST) $(MARKDOWNDOCS) $(LICENSE) $(TEMPLATES) \
            $(TOOLS) Makefile
	zip $@ $(SOURCES) $(TESTS) $(RUNTESTS) $(RUNTESTS_WIN) \
               $(INTEGRATIONTEST) $(MARKDOWNDOCS) $(LICENSE) $(TEMPLATES) \
               $(TOOLS) Makefile

bin-dist: $(BINDIST)

$(BINDIST): $(BINARY) $(MARKDOWNDOCS) $(LICENSE)
	zip $@ $(BINARY) $(MARKDOWNDOCS) $(LICENSE)

preview: $(PREVIEW)

$(PREVIEW): $(BINARY) $(SOURCES) $(TESTS) $(RUNTESTS) $(RUNTESTS_WIN) \
            $(INTEGRATIONTEST) $(MARKDOWNDOCS) $(LICENSE)
	zip $@ $(BINARY) $(SOURCES) $(TESTS) $(RUNTESTS) $(RUNTESTS_WIN) \
               $(INTEGRATIONTEST) $(MARKDOWNDOCS) $(LICENSE)

check: $(BINARY)
	-$(RUNTESTS)
	$(PYTHON) $(INTEGRATIONTEST) $(BINARY)

%.html : %.md
	pandoc -f markdown -t html -o $@ $<

html: $(HTMLDOCS) Makefile

clean:
	$(RM) -r $(BINARY) $(PREVIEW) $(HTMLDOCS)

distclean: clean
	$(RM) -r __pycache__ src/__pycache__ tests/scripttest/__pycache__ \
	$(wildcard src/*.pyc)

.PHONY: clean distclean check
.INTERMEDIATE: $(ZIP)
