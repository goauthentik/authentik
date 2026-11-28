---
name: locales
description: >
    Ship a UI language: turn it on in locales.yaml, fill the strings its catalogs are missing
    with a draft-then-review translation pass, and open the PR. Use when someone asks to "ship
    Swedish", "add a language", "enable a locale", "turn on <language> in the picker", "fill
    the missing translations", or links an issue asking for a translation to be shipped.
    Extracting new strings while writing code is in web/AGENTS.md, lint in linting, and PR
    conventions in contributing.
---

# Shipping a language

## Purpose

`locales.yaml` is the list of UI languages. A row with `ship: false` has catalogs in the tree
(`web/xliff/<tag>.xlf`, `locale/<django>/`) but isn't built or offered in the picker.
Shipping one means flipping that flag, then filling the strings added since the catalogs last
synced from Transifex, so the language doesn't launch with English gaps.

Steps are tagged: `[shell]` local command, `[agent]` delegated translation, `[verify]` check
before moving on. Earlier ship PRs: #24788 (Bengali), #26776 (Danish), #27580 (Latvian),
#28226 (Swedish).

## 1. Turn the language on

1. **[shell]** Branch from `origin/main` as `web/ship-<tag>`.
2. **[shell]** Set `ship: true` on the row in `locales.yaml`, then `make gen-locales`. It
   updates `web/lit-localize.json` and `web/src/common/ui/locale/definitions.ts`.
3. **[shell]** `pnpm --dir web run build-locales`. It regenerates `web/src/locale-codes.ts`,
   which `gen-locales` doesn't write.

## 2. Export what's missing

**[shell]** From `web/`, with a scratch directory outside the repo:

```sh
pnpm run fill-locale export <tag> <workdir> [batches=4]
```

It writes `batch<n>.json`: `[{key, source}]`. Keys are `web:<message id>` or `po:<msgid>`.

- Web placeholders appear as `{{0}}`, `{{1}}`: the n-th placeholder of the source message.
- Plural messages appear once per CLDR category the language has (`<id>.one`, `<id>.other`).
  Forms the language doesn't have are skipped.
- Backend plurals carry `plural` and `forms`. Their translation is an array with one string per
  form.

The script reads the catalog through lit-localize, so the count matches what the language
really lacks. `build-locales` also counts categories the language doesn't use, so its "missing"
number is higher.

## 3. Draft pass

**[agent]** One Haiku agent per batch, in parallel. Each writes `out<n>.json`: `{key: translation}`.
Give each agent:

- The product context: authentik is an identity provider, and the name stays lowercase and
  untranslated.
- The rules: keep every key and every placeholder (`{{n}}`, `%(name)s`, `{name}`, HTML,
  markdown), and match the catalog's register (formal or informal "you").
- The catalogs to grep for established terms first: `web/xliff/<tag>.xlf` and
  `locale/<django>/LC_MESSAGES/django.po`.
- To list the items it was unsure of in its reply.

**[verify]** `pnpm run fill-locale merge <tag> <workdir> --check`. It rejects missing keys,
changed placeholders and wrong plural form counts. Send failures back to the agent that wrote
them.

**[shell]** `pnpm run fill-locale merge <tag> <workdir>`. It writes the web catalog through
lit-localize, regroups the plural forms, writes the `.po` file with Transifex's line wrapping,
and compiles the `.mo` file with `manage compilemessages`. The `.po` side reads the catalog with
`@goauthentik/lexicon-audit`'s readers.

**[verify]** Audit the language's catalogs for vulgar or offensive wording. A model can produce
it without meaning to:

```sh
pnpm --dir packages/lexicon-audit exec lexicon-audit audit --locale <tag> ../../locale ../../web/xliff
```

The audit needs `packages/lexicon-audit/out/lexicon-audit.db`. Build it from a local corpus
(`lexicon-audit build`), or decrypt the sealed copy with `LEXICON_AUDIT_PASSPHRASE` set
(`lexicon-audit unseal`). By default it prints counts only. If it finds anything, rerun with
`--report <dir>` outside the repo, fix the strings in `out*.json`, and merge again. Never paste
the matched text into a commit, PR or log. Then commit.

## 4. Review pass

**[agent]** One stronger-model agent reviews every draft against the sources and the catalog.
It writes `corrections.json`: `{key: {old, new, why}}`, with only the keys it changes. Ask it
to check:

- **Terminology** against the catalog's majority usage, not a single hit. The drafts are in
  the catalog by now too.
- **Placeholder meaning**: grep `web/src` for the message ID to see whether `{{0}}` is a count,
  a name or a noun. Agreement errors hide there, e.g. a fixed article in front of a noun
  placeholder.
- **Every plural pair**, and singular vs plural in the `verbose-name` labels.
- **The draft agents' doubts**, and anything a native speaker should decide.

**[shell]** `pnpm run fill-locale merge <tag> <workdir> --corrections`. Run the audit again,
then commit.

## 5. Check and open the PR

1. **[verify]** `akdev_lint` and `akdev_generated` (or `make lint-changed` and `make check-gen`).
2. **[shell]** Draft PR titled `web/i18n: ship <Language> (<tag>)`, following the
   contributing skill. Under "AI disclosure", say which models drafted and reviewed the
   strings, and list the terms left for a native speaker. Leave the `make all` box unticked
   unless you ran it.

## Gotchas

- **Only the shipped language's catalogs change.** The export and merge read every catalog
  but write only `<tag>`'s files. Don't run `extract-locales` for this: it rewrites every
  language's XLIFF file, and those changes belong to Transifex.
- **`gen-locales` doesn't write `web/src/locale-codes.ts`.** Only the lit-localize build does
  (step 1.3).
- **The same English text can need two translations.** For example, "Rättigheter" was already
  Swedish for *permissions*, so it couldn't also be used for *entitlements*. The review pass
  catches these. The draft pass won't.
- **Ellipsis and punctuation follow the catalog**, even when it's inconsistent. Leave a
  cleanup of the whole catalog to its own PR.
