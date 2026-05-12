# authentik WebUI

This is the default UI for the authentik server. The documentation is going to be a little sparse
for awhile, but at least let's get started.

# Setup

Install dependencies from the repo root with `make node-install` (or `make install` for the full
Python + web + docs bootstrap). This wraps `npm ci` and explicitly rebuilds the small set of
packages whose install scripts are required for the toolchain to function — currently `esbuild`,
`chromedriver`, `tree-sitter`, and `tree-sitter-json`.

The repo-root `.npmrc` sets `ignore-scripts=true` to neutralize the dominant npm supply-chain
attack vector. As a side effect, running `npm ci` directly in this directory will install
dependencies but skip those rebuilds, leaving `esbuild` and `chromedriver` in a non-functional
state. If you bypass `make`, run the rebuild step yourself:

```bash
npm rebuild --ignore-scripts=false --foreground-scripts \
    esbuild chromedriver tree-sitter tree-sitter-json
```

New dependencies that ship install scripts must be audited and added to `TRUSTED_INSTALL_SCRIPTS`
in the repo-root `Makefile`. Each entry is arbitrary code that runs at install time, so the list
is intentionally small.

## Optional: containerized installs (macOS)

If you're on **macOS 15+ on Apple Silicon** and want kernel-level isolation on top of
`ignore-scripts`, run:

```bash
make node-install-containerized
```

This runs the install inside an ephemeral Linux microVM via Apple's [`container`
runtime](https://github.com/apple/container). The container sees the repo at `/work` and nothing
else — no `~/.ssh`, no `~/.aws`, no Keychain, no other process on your machine. If a transitive
dependency does something unexpected during install, the blast radius is the container's lifetime.

Install once:

```bash
brew install container
```

**Workflow tradeoff:** the container is Linux, not Darwin. `node_modules` installed inside will
contain `linux-arm64` binaries (esbuild, chromedriver, tree-sitter, …). If you also want to run
the dev server natively on macOS for IDE integration, you'll need a second native install via
`make node-install`. Pick one workflow per session — they share a `node_modules` directory and
overwrite each other.

For finer-grained control:

- `CONTAINER_NETWORK=none scripts/container-sandbox npm test` — drop network for test runs
- `CONTAINER_IMAGE=node:22-bookworm@sha256:... make node-install-containerized` — pin by digest

This path is opt-in. The default `make node-install` is portable and identical across platforms.
The `.npmrc` baseline applies in both cases.

# The Theory of the authentik UI

In Peter Naur's 1985 essay [Programming as Theory
Building](https://pages.cs.wisc.edu/~remzi/Naur.pdf), programming is described as creating a mental
model of how a program _should_ run, then writing the code to test if the program _can_ run that
way.

The mental model for the authentik UI is straightforward. There are five "applications" within the
UI, each with its own base URL, router, and responsibilities, and each application needs as many as
three contexts in which to run.

The three contexts corresponds to objects in the API's `model` section, so let's use those names.

- The root `Config`. The root configuration object of the server, containing mostly caching and
  error reporting information. This is misleading, however; the `Config` object contains some user
  information, specifically a list of permissions the current user (or "no user") has.
- The root `CurrentTenant`. This describes the `Brand` information UIs should use, such as themes,
  logos, favicon, and specific default flows for logging in, logging out, and recovering a user
  password.
- The current `SessionUser`, the person logged in: username, display name, and various states.
  (Note: the authentik server permits administrators to "impersonate" any other user in order to
  debug their authentication experience. If impersonation is active, the `user` field reflects that
  user, but it also includes a field, `original`, with the administrator's information.)

(There is a fourth context object, Version, but its use is limited to displaying version information
and checking for upgrades. Just be aware that you will see it, but you will probably never interact
with it.)

There are five applications. Two (`loading` and `api-browser`) are trivial applications whose
insides are provided by third-party libraries (Patternfly and Rapidoc, respectively). The other
three are actual applications. The descriptions below are wholly from the view of the user's
experience:

- `Flow`: From a given URL, displays a form that requests information from the user to accomplish a
  task. Some tasks require the user to be logged in, but many (such as logging in itself!)
  obviously do not.
- `User`: Provides the user with access to the applications they can access, plus a few user
  settings.
- `Admin`: Provides someone with super-user permissions access to the administrative functions of
  the authentik server.

**Mental Model**

- Upon initialization, _every_ authentik UI application fetches `Config` and `CurrentTenant`. `User`
  and `Admin` will also attempt to load the `SessionUser`; if there is none, the user is kicked out
  to the `Flow` for logging into authentik itself.
- `Config`, `CurrentTenant`, and `SessionUser`, are provided by the `@goauthentik/api` application,
  not by the codebase under `./web`. (Where you are now).
- `Flow`, `User`, and `Admin` are all called `Interfaces` and are found in
  `./web/src/flow/FlowInterface`, `./web/src/user/UserInterface`, `./web/src/admin/AdminInterface`,
  respectively.

Inside each of these you will find, in a hierarchal order:

- The context layer described above
    - A theme managing layer
    - The orchestration layer:
        - web socket handler for server-generated events
        - The router
            - Individual routes for each vertical slice and its relationship to other objects:

Each slice corresponds to an object table on the server, and each slice _usually_ consists of the
following:

- A paginated collection display, usually using the `Table` foundation (found in
  `./web/src/elements/Table`)
- The ability to view an individual object from the collection, which you may be able to:
    - Edit
    - Delete
- A form for creating a new object
- Tabs showing that object's relationship to other objects
    - Interactive elements for changing or deleting those relationships, or creating new ones.
    - The ability to create new objects with which to have that relationship, if they're not part of
      the core objects (such as User->MFA authenticator apps, since the latter is not a "core" object
      and has no tab of its own).

We are still a bit "all over the place" with respect to sub-units and common units; there are
folders `common`, `elements`, and `components`, and ideally they would be:

- `common`: non-UI related libraries all of our applications need
- `elements`: UI elements shared among multiple applications that do not need context
- `components`: UI elements shared among multiple that use one or more context

... but at the moment there are some context-sensitive elements, and some UI-related stuff in
`common`.

# Comments

**NOTE:** The comments in this section are for specific changes to this repository that cannot be
reliably documented any other way. For the most part, they contain comments related to custom
settings in JSON files, which do not support comments.

- `tsconfig.json`:
    - `compilerOptions.useDefineForClassFields: false` is required to make TSC use the "classic" form
      of field definition when compiling class definitions. Storybook does not handle the ESNext
      proposed definition mechanism (yet).
    - `compilerOptions.plugins.ts-lit-plugin.rules.no-unknown-tag-name: "off"`: required to support
      rapidoc, which exports its tag late.
    - `compilerOptions.plugins.ts-lit-plugin.rules.no-missing-import: "off"`: lit-analyzer currently
      does not support path aliases very well, and cannot find the definition files associated with
      imports using them.
    - `compilerOptions.plugins.ts-lit-plugin.rules.no-incompatible-type-binding: "warn"`: lit-analyzer
      does not support generics well when parsing a subtype of `HTMLElement`. As a result, this threw
      too many errors to be supportable.

### License

This code is licensed under the [MIT License](https://www.tldrlegal.com/license/mit-license).
[A copy of the license](./LICENSE.txt) is included with this project.
