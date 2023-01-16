.PHONY: help
help:
	@echo "localize ... Update translation files"

.PHONY: localize
localize:
	xgettext --from-code=UTF-8 --omit-header --force-po --no-wrap --no-location --keyword=_:2 -o src/po/messages.pot `find src/ -name "*.py"`
	msgmerge --previous -o src/po/cs.po src/po/cs.po src/po/messages.pot --force-po --no-wrap
	msgmerge --previous -o src/po/sk.po src/po/sk.po src/po/messages.pot --force-po --no-wrap
	sed -r '/^#(,|)(.*)/d' -i -s src/po/*.po
