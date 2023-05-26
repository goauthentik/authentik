# po2xliff4lit: Convert a PO-based locale project to one suitable to lit-localize

Recently, I needed to convert a project that was both React and PO-based to use Lit and
Lit-Localize.  We had extensive PO files, and I needed to convert them.  Lit using the XLIFF (XML
Language Interchange File) format, and not just that format, but a very specific subset for doing
templatized strings with variable substitution.

This script is the outcome of that effort.

# Usage

This is a very specific use-case.  It assumes you have (a) a pre-existing collection of PO files
that you need to convert, have already configured your working Lit program to use Lit-localize, and
have run `lit-localize extract`, thus creating your collection of (source-only) XLIFF files for each
locale you want to support.

Assuming you have your generated `xliff` folder and your existing PO files in the `locales` folder,
the sequence I followed was:

``` bash
# (In your $PROJECT folder)
$ mv xliff xliff-generated
$ mkdir xliff
# (In this folder):
$ node bin/index.js -x $PROJECT/xliff-generated/de.xlf -p $PROJECT/locales/de.po | tidy -indent -xml -wrap 0 > xliff/de.xlf
```

And you can replace that last line with:

``` bash
for i in $PROJECT/xliff-generated/*.xlf; do \
    F=$(basename $i | sed 's/\.xlf//') ; \
    node bin/index.js -x $PROJECT/xliff-generated/$F.xlf -p $PROJECT/$F.po | tidy -indent -xml -wrap 0 > $PROJECT/xliff/$F.xlf ; \
done
```

# Notes

## Known Gotchas / Issues

If your PO file's `msgid` includes a parameterized string, but there is no corresponding `msgstr`
for that `msgid`, the `lit-localize build` function may fail due to an empty target. A missing
target creates only a warning. Remove all empty `<target/>`s in your `.xlf` files with the following
commands:

``` bash
$  perl -pi.bak -e 's/\<target\/\>//' *.xlf
$  perl -pi.bak -e 's/\<target\><\/target\>//' *.xlf
```

## Autamatically moving away from Lingui

I was moving this project from `lingui`, so here are some tips.

If you're already in your source folder, the following shell command, which depends upon both Perl
and Ripgrep, will replace every instance of lingui's `t` macro with Lit-localize's `msg()` function.
They must be run in order; the first finds every instance of `t` that includes a parameterized
variable; the second translates all those that do not. If you have parameterized strings that also
include HTML, well, I didn't, so you'll have to figure that out on your own. The `-t ts` argument to
RipGrep means "process only Typescript files"; this skips the redundancy of reprocessing the backup
files Perl creates.

``` bash
$ for i in $(rg -t ts -l 't`[^`]*\$\{[^`]*`' .) ; do perl -pi.bak -e 's/t`([^`]*?\$\{[^`]*?)`/msg(str`\1`)/g' $i ; done
$ for i in $(rg -t ts -l 't`.*?`'); do perl -pi.bak -e 's/t`([^`]*?)`/msg("\1")/' $i ; done
$ for i in $(rg -t ts -l 'msg\(str' .); do perl -pi.bak -e 's/import { t } from "\@lingui\/macro";/import { msg, str } from "\@lit\/localize";/' $i ; done
$ for i in $(rg -t ts -l 'msg\("' .); do perl -pi.bak -e 's/import { t } from "\@lingui\/macro";/import { msg } from "\@lit\/localize";/' $i ; done
```

To remove all your backup files:

``` bash
$ find . name '*.bak' -exec rm {} \;
```

