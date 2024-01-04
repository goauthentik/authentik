# authentik WebUI

This is the default UI for the authentik server. The documentation is going to be a little sparse
for awhile, but at least let's get started.

# Comments

**NOTE:** The comments in this section are for specific changes to this repository that cannot be
reliably documented any other way. For the most part, they contain comments related to custom
settings in JSON files, which do not support comments.

-   `tsconfig.json`:
    -   `compilerOptions.useDefineForClassFields: false` is required to make TSC use the "classic" form
        of field definition when compiling class definitions. Storybook does not handle the ESNext
        proposed definition mechanism (yet).
    -   `compilerOptions.plugins.ts-lit-plugin.rules.no-unknown-tag-name: "off"`: required to support
        rapidoc, which exports its tag late.
    -   `compilerOptions.plugins.ts-lit-plugin.rules.no-missing-import: "off"`: lit-analyzer currently
        does not support path aliases very well, and cannot find the definition files associated with
        imports using them.
    -   `compilerOptions.plugins.ts-lit-plugin.rules.no-incompatible-type-binding: "warn"`: lit-analyzer
        does not support generics well when parsing a subtype of `HTMLElement`. As a result, this threw
        too many errors to be supportable.
