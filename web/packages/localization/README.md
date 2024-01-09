web: localization

This package contains all the localization strings needed by all of the other packages in our
application, and provides tooling for making them available as JavaScript translation catalogs
suitable for `lit-localize`. It does this by scanning the source trees of all of the packages and
assembling the complete list of translatable (and already translated) strings into the `./xliff`
folder.

Commands provided:

- extract-locales: extracts any string tagged as translatable (i.e., with the `msg(...)` syntax) and
  integrates any newfound strings into the existing XLIFF files. Also: reprocesses the
  `sourceLocale` file to create a pseudolocale for testing purposes. (This must be done
  sequentially, as the `sourceLocale` file must be built before the conversion takes place.)
- build: Convert XLIFF to Typescript, compile, lint, and format. The `lint` pass is especially
  important as it enforces the "backquotes to doublequotes when no template in use" rule, and the
  `format` pass must always come last to ensure our committed code matches our standard.
- clean: Delete the `dist` and `src` folders, as well as the constructed `.mjs` file for
  pseudolocalization.
  
## User notes:

Due to the circular nature of translation's dependencies (*every* package must be scanned for new
strings, and if there are new strings, *every* package must then be rebuilt), extraction is not
performed automatically. This introduces the risk that a developer may not run the extraction and
test as needed. The reminder in the GitHub pull request template is there for a reason.

## Maintenance note:

If you add a new package to the monorepo and it has strings that need translating, you must add it
to the list of `inputFiles` scanned in `lit-localize.json`.


