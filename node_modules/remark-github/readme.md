# remark-github

[![Build][build-badge]][build]
[![Coverage][coverage-badge]][coverage]
[![Downloads][downloads-badge]][downloads]
[![Size][size-badge]][size]
[![Sponsors][sponsors-badge]][collective]
[![Backers][backers-badge]][collective]
[![Chat][chat-badge]][chat]

**[remark][]** plugin to link references to commits, issues, and users, in the
same way that GitHub does in comments, issues, PRs, and releases (see [Writing
on GitHub][github-writing]).

## Contents

*   [What is this?](#what-is-this)
*   [When should I use this?](#when-should-i-use-this)
*   [Install](#install)
*   [Use](#use)
*   [API](#api)
    *   [`defaultBuildUrl(values)`](#defaultbuildurlvalues)
    *   [`unified().use(remarkGithub[, options])`](#unifieduseremarkgithub-options)
    *   [`BuildUrl`](#buildurl)
    *   [`BuildUrlCommitValues`](#buildurlcommitvalues)
    *   [`BuildUrlCompareValues`](#buildurlcomparevalues)
    *   [`BuildUrlIssueValues`](#buildurlissuevalues)
    *   [`BuildUrlMentionValues`](#buildurlmentionvalues)
    *   [`BuildUrlValues`](#buildurlvalues)
    *   [`Options`](#options)
*   [Examples](#examples)
    *   [Example: `buildUrl`](#example-buildurl)
*   [Syntax](#syntax)
*   [Types](#types)
*   [Compatibility](#compatibility)
*   [Security](#security)
*   [Related](#related)
*   [Contribute](#contribute)
*   [License](#license)

## What is this?

This package is a [unified][] ([remark][]) plugin to link references to commits,
issues, and users: `@wooorm` -> `[**@wooorm**](https://github.com/wooorm)`.

## When should I use this?

This project is useful if you want to emulate how markdown would work in GitHub
comments, issues, PRs, or releases, but it’s actually displayed somewhere else
(on a website, or in other places on GitHub which don’t link references, such as
markdown in a repo or Gist).
This plugin does not support other platforms such as GitLab or Bitbucket and
their custom features.

A different plugin, [`remark-gfm`][remark-gfm], adds support for GFM (GitHub
Flavored Markdown).
GFM is a set of extensions (autolink literals, footnotes, strikethrough, tables,
and tasklists) to markdown that are supported everywhere on GitHub.

Another plugin, [`remark-breaks`][remark-breaks], turns soft line endings
(enters) into hard breaks (`<br>`s).
GitHub does this in a few places (comments, issues, PRs, and releases), but it’s
not semantic according to HTML and not compliant to markdown.

Yet another plugin, [`remark-frontmatter`][remark-frontmatter], adds support
for YAML frontmatter.
GitHub supports frontmatter for files in Gists and repos.

## Install

This package is [ESM only][esm].
In Node.js (version 16+), install with [npm][]:

```sh
npm install remark-github
```

In Deno with [`esm.sh`][esmsh]:

```js
import remarkGithub, {defaultBuildUrl} from 'https://esm.sh/remark-github@12'
```

In browsers with [`esm.sh`][esmsh]:

```html
<script type="module">
  import remarkGithub, {defaultBuildUrl} from 'https://esm.sh/remark-github@12?bundle'
</script>
```

## Use

Say we have the following file `example.md`:

```markdown
Some references:

*   Commit: f8083175fe890cbf14f41d0a06e7aa35d4989587
*   Commit (fork): foo@f8083175fe890cbf14f41d0a06e7aa35d4989587
*   Commit (repo): remarkjs/remark@e1aa9f6c02de18b9459b7d269712bcb50183ce89
*   Issue or PR (`#`): #1
*   Issue or PR (`GH-`): GH-1
*   Issue or PR (fork): foo#1
*   Issue or PR (project): remarkjs/remark#1
*   Mention: @wooorm

Some links:

*   Commit: <https://github.com/remarkjs/remark/commit/e1aa9f6c02de18b9459b7d269712bcb50183ce89>
*   Commit comment: <https://github.com/remarkjs/remark/commit/ac63bc3abacf14cf08ca5e2d8f1f8e88a7b9015c#commitcomment-16372693>
*   Issue or PR: <https://github.com/remarkjs/remark/issues/182>
*   Issue or PR comment: <https://github.com/remarkjs/remark-github/issues/3#issue-151160339>
*   Mention: <https://github.com/ben-eb>
```

…and a module `example.js`:

```js
import {remark} from 'remark'
import remarkGfm from 'remark-gfm'
import remarkGithub from 'remark-github'
import {read} from 'to-vfile'

const file = await remark()
  .use(remarkGfm)
  .use(remarkGithub)
  .process(await read('example.md'))

console.log(String(file))
```

…then running `node example.js` yields:

```markdown
Some references:

* Commit: [`f808317`](https://github.com/remarkjs/remark-github/commit/f8083175fe890cbf14f41d0a06e7aa35d4989587)
* Commit (fork): [foo@`f808317`](https://github.com/foo/remark-github/commit/f8083175fe890cbf14f41d0a06e7aa35d4989587)
* Commit (repo): [remarkjs/remark@`e1aa9f6`](https://github.com/remarkjs/remark/commit/e1aa9f6c02de18b9459b7d269712bcb50183ce89)
* Issue or PR (`#`): [#1](https://github.com/remarkjs/remark-github/issues/1)
* Issue or PR (`GH-`): [GH-1](https://github.com/remarkjs/remark-github/issues/1)
* Issue or PR (fork): [foo#1](https://github.com/foo/remark-github/issues/1)
* Issue or PR (project): [remarkjs/remark#1](https://github.com/remarkjs/remark/issues/1)
* Mention: [**@wooorm**](https://github.com/wooorm)

Some links:

* Commit: [remarkjs/remark@`e1aa9f6`](https://github.com/remarkjs/remark/commit/e1aa9f6c02de18b9459b7d269712bcb50183ce89)
* Commit comment: [remarkjs/remark@`ac63bc3` (comment)](https://github.com/remarkjs/remark/commit/ac63bc3abacf14cf08ca5e2d8f1f8e88a7b9015c#commitcomment-16372693)
* Issue or PR: [remarkjs/remark#182](https://github.com/remarkjs/remark/issues/182)
* Issue or PR comment: [#3 (comment)](https://github.com/remarkjs/remark-github/issues/3#issue-151160339)
* Mention: <https://github.com/ben-eb>
```

## API

This package exports the identifier [`defaultBuildUrl`][api-default-build-url].
The default export is [`remarkGithub`][api-remark-github].

### `defaultBuildUrl(values)`

Create a URL to GH.

###### Parameters

*   `values` ([`BuildUrlValues`][api-build-url-values])
    — info on the link to build

###### Returns

URL to use (`string`).

### `unified().use(remarkGithub[, options])`

Link references to users, commits, and issues, in the same way that GitHub does
in comments, issues, PRs, and releases.

###### Parameters

*   `options` ([`Options`][api-options], optional)
    — configuration

###### Returns

Transform ([`Transformer`][unified-transformer]).

### `BuildUrl`

Create a URL (TypeScript type).

###### Parameters

*   `values` ([`BuildUrlValues`][api-build-url-values])
    — info on the link to build

###### Returns

URL to use or `false` to not link (`string | false`).

### `BuildUrlCommitValues`

Info for commit hash (TypeScript type).

###### Fields

*   `hash` (`string`)
    — commit hash value
*   `project` (`string`)
    — project name
*   `type` (`'commit'`)
    — kind
*   `user` (`string`)
    — owner of repo

### `BuildUrlCompareValues`

Info for commit hash ranges (TypeScript type).

###### Fields

*   `base` (`string`)
    — SHA of the range start
*   `compare` (`string`)
    — SHA of the range end
*   `project` (`string`)
    — project name
*   `type` (`'compare'`)
    — kind
*   `user` (`string`)
    — owner of repo

### `BuildUrlIssueValues`

Info for issues (TypeScript type).

###### Fields

*   `no` (`string`)
    — issue number
*   `project` (`string`)
    — project name
*   `type` (`'issue'`)
    — kind
*   `user` (`string`)
    — owner of repo

### `BuildUrlMentionValues`

Info for mentions (TypeScript type).

###### Fields

*   `type` (`'mention'`)
    — kind
*   `user` (`string`)
    — user name

### `BuildUrlValues`

Info (TypeScript type).

###### Type

```ts
type BuildUrlValues =
  | BuildUrlCommitValues
  | BuildUrlCompareValues
  | BuildUrlIssueValues
  | BuildUrlMentionValues
```

### `Options`

Configuration (TypeScript type).

###### Fields

*   `buildUrl` ([`BuildUrl`][api-build-url], default:
    [`defaultBuildUrl`][api-default-build-url])
    — change how things are linked
*   `mentionStrong` (`boolean`, default: `true`)
    — wrap mentions in `strong`;
    this makes them render more like how GitHub styles them, but GH itself
    uses CSS instead of `strong`
*   `repository` (`string`, default: `repository` from `packag.json` in CWD in
    Node, otherwise required)
    — repository to link against;
    should point to a GitHub repository (such as `'user/project'`)

## Examples

### Example: `buildUrl`

A `buildUrl` can be passed to not link mentions.
For example, by changing `example.js` from before like so:

```diff
@@ -1,11 +1,15 @@
 import {remark} from 'remark'
 import remarkGfm from 'remark-gfm'
-import remarkGithub from 'remark-github'
+import remarkGithub, {defaultBuildUrl} from 'remark-github'
 import {read} from 'to-vfile'

 const file = await remark()
   .use(remarkGfm)
-  .use(remarkGithub)
+  .use(remarkGithub, {
+    buildUrl(values) {
+      return values.type === 'mention' ? false : defaultBuildUrl(values)
+    }
+  })
   .process(await read('example.md'))

 console.log(String(file))
```

To instead point mentions to a different place, change `example.js` like so:

```diff
@@ -1,11 +1,17 @@
 import {remark} from 'remark'
 import remarkGfm from 'remark-gfm'
-import remarkGithub from 'remark-github'
+import remarkGithub, {defaultBuildUrl} from 'remark-github'
 import {read} from 'to-vfile'

 const file = await remark()
   .use(remarkGfm)
-  .use(remarkGithub)
+  .use(remarkGithub, {
+    buildUrl(values) {
+      return values.type === 'mention'
+        ? `https://yourwebsite.com/${values.user}/`
+        : defaultBuildUrl(values)
+    }
+  })
   .process(await read('example.md'))

 console.log(String(file))
```

## Syntax

The following references are supported:

*   Commits:
    `1f2a4fb` →
    [`1f2a4fb`][github-sha]
*   Commits across forks:
    `remarkjs@1f2a4fb` →
    [remarkjs@`1f2a4fb`][github-sha]
*   Commits across projects:
    `remarkjs/remark-github@1f2a4fb` →
    [remarkjs/remark-github@`1f2a4fb`][github-sha]
*   Compare ranges:
    `e2acebc...2aa9311` →
    [`e2acebc...2aa9311`][github-sha-range]
*   Compare ranges across forks:
    `remarkjs@e2acebc...2aa9311` →
    [remarkjs/remark-github@`e2acebc...2aa9311`][github-sha-range]
*   Compare ranges across projects:
    `remarkjs/remark-github@e2acebc...2aa9311` →
    [remarkjs/remark-github@`e2acebc...2aa9311`][github-sha-range]
*   Prefix issues:
    `GH-1` →
    [GH-1][github-issue]
*   Hash issues:
    `#1` →
    [#1][github-issue]
*   Issues across forks:
    `remarkjs#1` →
    [remarkjs#1][github-issue]
*   Issues across projects:
    `remarkjs/remark-github#1` →
    [remarkjs/remark-github#1][github-issue]
*   At-mentions:
    `@wooorm` →
    [**@wooorm**][github-mention]

Autolinks to these references are also transformed:
`https://github.com/wooorm` -> `[**@wooorm**](https://github.com/wooorm)`

## Types

This package is fully typed with [TypeScript][].
It exports the additional types
[`BuildUrl`][api-build-url],
[`BuildUrlCommitValues`][api-build-url-commit-values],
[`BuildUrlCompareValues`][api-build-url-compare-values],
[`BuildUrlIssueValues`][api-build-url-issue-values],
[`BuildUrlMentionValues`][api-build-url-mention-values],
[`BuildUrlValues`][api-build-url-values],
[`DefaultBuildUrl`][api-default-build-url],
[`Options`][api-options].

## Compatibility

Projects maintained by the unified collective are compatible with maintained
versions of Node.js.

When we cut a new major release, we drop support for unmaintained versions of
Node.
This means we try to keep the current release line, `remark-github@^12`,
compatible with Node.js 16.

This plugin works with `unified` version 6+ and `remark` version 7+.

## Security

Use of `remark-github` does not involve **[rehype][]** (**[hast][]**).
It does inject links based on user content, but those links only go to GitHub.
There are no openings for [cross-site scripting (XSS)][wiki-xss] attacks.

## Related

*   [`remark-gfm`][remark-gfm]
    — support GFM (autolink literals, footnotes, strikethrough, tables,
    tasklists)
*   [`remark-breaks`][remark-breaks]
    — support breaks without needing spaces or escapes (enters to `<br>`)
*   [`remark-frontmatter`][remark-frontmatter]
    — support frontmatter (YAML, TOML, and more)

## Contribute

See [`contributing.md`][contributing] in [`remarkjs/.github`][health] for ways
to get started.
See [`support.md`][support] for ways to get help.

This project has a [code of conduct][coc].
By interacting with this repository, organization, or community you agree to
abide by its terms.

## License

[MIT][license] © [Titus Wormer][author]

<!-- Definitions -->

[build-badge]: https://github.com/remarkjs/remark-github/workflows/main/badge.svg

[build]: https://github.com/remarkjs/remark-github/actions

[coverage-badge]: https://img.shields.io/codecov/c/github/remarkjs/remark-github.svg

[coverage]: https://codecov.io/github/remarkjs/remark-github

[downloads-badge]: https://img.shields.io/npm/dm/remark-github.svg

[downloads]: https://www.npmjs.com/package/remark-github

[size-badge]: https://img.shields.io/bundlejs/size/remark-github

[size]: https://bundlejs.com/?q=remark-github

[sponsors-badge]: https://opencollective.com/unified/sponsors/badge.svg

[backers-badge]: https://opencollective.com/unified/backers/badge.svg

[collective]: https://opencollective.com/unified

[chat-badge]: https://img.shields.io/badge/chat-discussions-success.svg

[chat]: https://github.com/remarkjs/remark/discussions

[npm]: https://docs.npmjs.com/cli/install

[esm]: https://gist.github.com/sindresorhus/a39789f98801d908bbc7ff3ecc99d99c

[esmsh]: https://esm.sh

[health]: https://github.com/remarkjs/.github

[contributing]: https://github.com/remarkjs/.github/blob/main/contributing.md

[support]: https://github.com/remarkjs/.github/blob/main/support.md

[coc]: https://github.com/remarkjs/.github/blob/main/code-of-conduct.md

[license]: license

[author]: https://wooorm.com

[github-issue]: https://github.com/remarkjs/remark-github/issues/1

[github-mention]: https://github.com/wooorm

[github-sha]: https://github.com/remarkjs/remark-github/commit/1f2a4fb8f88a0a98ea9d0c0522cd538a9898f921

[github-sha-range]: https://github.com/wooorm/remark/compare/e2acebc...2aa9311

[github-writing]: https://docs.github.com/en/github/writing-on-github#references

[hast]: https://github.com/syntax-tree/hast

[rehype]: https://github.com/rehypejs/rehype

[remark]: https://github.com/remarkjs/remark

[remark-gfm]: https://github.com/remarkjs/remark-gfm

[remark-breaks]: https://github.com/remarkjs/remark-breaks

[remark-frontmatter]: https://github.com/remarkjs/remark-frontmatter

[typescript]: https://www.typescriptlang.org

[unified]: https://github.com/unifiedjs/unified

[unified-transformer]: https://github.com/unifiedjs/unified#transformer

[wiki-xss]: https://en.wikipedia.org/wiki/Cross-site_scripting

[api-options]: #options

[api-remark-github]: #unifieduseremarkgithub-options

[api-build-url]: #buildurl

[api-build-url-commit-values]: #buildurlcommitvalues

[api-build-url-compare-values]: #buildurlcomparevalues

[api-build-url-issue-values]: #buildurlissuevalues

[api-build-url-mention-values]: #buildurlmentionvalues

[api-build-url-values]: #buildurlvalues

[api-default-build-url]: #
