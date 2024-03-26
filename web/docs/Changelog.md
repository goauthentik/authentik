### 2024-03-26T09:25:06-0700

Split the tsconfig file into a base and build variant.

Lesson: This lesson is stored here and not in a comment in tsconfig.json because
JSON doesn't like comments. Doug Crockford's purity requirement has doomed an
entire generation to keeping its human-facing meta somewhere other than in the
file where it belongs.

Lesson: The `extend` command of tsconfig has an unexpected behavior. It is
neither a merge or a replace, but some mixture of the two. The buildfile's
`compilerOptions` is not a full replacement; instead, each of _its_ top-level
fields is a replacement for what is found in the basefile. So while you don't
need to include _everything_ in a `compilerOptions` field if you want to change
one thing, if you want to modify _one_ path in `compilerOptions.path`, you must
include the entire `compilerOptions.path` collection in your buildfile.
g
