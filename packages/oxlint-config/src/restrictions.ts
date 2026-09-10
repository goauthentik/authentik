/**
 * @file Platform-layering import restrictions, ported to oxlint's `no-restricted-imports`.
 */

import { builtinModules } from "node:module";

//#region Runtime data

/**
 * Reserved package-name suffixes mapped to their target runtime.
 *
 * A package whose final name segment matches one of these signals that runtime, and imports across incompatible runtime
 * boundaries become lint errors.
 */
export const RuntimePackageNamesRecord = {
    browser: ["client", "browser"],
    node: ["server", "node", "sdk"],
    agnostic: ["shared", "common"],
    worker: ["worker"],
} as const;

export type RuntimePackageNamesRecord = typeof RuntimePackageNamesRecord;

/** Valid runtime names. */
export type RuntimeName = keyof RuntimePackageNamesRecord;

/**
 * Given a package name, produces the glob matcher for files belonging to that package.
 *
 * @param packageName The final package-name segment, e.g. `client`.
 *
 * @returns A single-element glob array, e.g. `["**\/client.{js,...}"]`.
 */
export function createPackageFileMatcher(packageName: string): string[] {
    return [`**/${packageName}.{js,mjs,cjs,ts,d.ts,mts,tsx}`];
}

/** Joins a namespace and package name into a specifier, e.g. `@goauthentik/client`. */
function namespaced(packageNamespace: string, packageName: string): string {
    return [packageNamespace, packageName].filter(Boolean).join("/");
}

//#endregion

//#region Node built-in helpers

const NODE_BUILTINS_NO_PREFIX = builtinModules.filter(
    (moduleName) => !moduleName.startsWith("_") && !moduleName.startsWith("node:"),
);

const NODE_BUILTINS_PREFIXED = NODE_BUILTINS_NO_PREFIX.map((moduleName) => `node:${moduleName}`);

/** A restricted-import entry: an exact module name plus the message shown when it is imported. */
export interface RestrictedPath {
    name: string;
    message: string;
}

/**
 * Unprefixed Node built-ins (e.g. `fs`), each nudging toward the `node:` prefix. Used by browser- and node-runtime
 * files where the bare form is ambiguous.
 */
export function ambiguousNodeBuiltinPaths(): RestrictedPath[] {
    return NODE_BUILTINS_NO_PREFIX.map((name) => ({
        name,
        message: `Ambiguous module: did you mean \`node:${name}\`?`,
    }));
}

/**
 * Every Node built-in (prefixed and unprefixed), each carrying the given message. Used by agnostic-runtime files, which
 * must not assume a Node runtime at all.
 */
export function allNodeBuiltinPaths(message: string): RestrictedPath[] {
    return [...NODE_BUILTINS_NO_PREFIX, ...NODE_BUILTINS_PREFIXED].map((name) => ({
        name,
        message,
    }));
}

//#endregion

//#region Browser globals

/**
 * Browser globals whose bare use is ambiguous (they collide with common identifiers). Browser- and node-runtime files
 * warn on these, nudging toward an explicit `window.` access.
 */
const BROWSER_GLOBALS = [
    "addEventListener",
    "blur",
    "close",
    "closed",
    "confirm",
    "defaultStatus",
    "defaultstatus",
    "event",
    "external",
    "find",
    "focus",
    "frameElement",
    "frames",
    "history",
    "innerHeight",
    "innerWidth",
    "length",
    "location",
    "locationbar",
    "menubar",
    "moveBy",
    "moveTo",
    "name",
    "onblur",
    "onerror",
    "onfocus",
    "onload",
    "onresize",
    "onunload",
    "open",
    "opener",
    "opera",
    "outerHeight",
    "outerWidth",
    "pageXOffset",
    "pageYOffset",
    "parent",
    "print",
    "removeEventListener",
    "resizeBy",
    "resizeTo",
    "screen",
    "screenLeft",
    "screenTop",
    "screenX",
    "screenY",
    "scroll",
    "scrollbars",
    "scrollBy",
    "scrollTo",
    "scrollX",
    "scrollY",
    "self",
    "status",
    "statusbar",
    "stop",
    "toolbar",
    "top",
] as const;

function restrictedBrowserGlobalsRule(): unknown {
    return [
        "warn",
        ...BROWSER_GLOBALS.map((name) => ({
            name,
            message: `Ambiguous: did you mean \`window.${name}\`?`,
        })),
    ];
}

//#endregion

//#region Override generation

/** A per-file-glob oxlint override: applies `rules` only to files matching `files`. */
export interface OxlintOverride {
    files: string[];
    rules: Record<string, unknown>;
}

/** A restricted-import pattern: a set of gitignore-style globs plus a message. */
interface RestrictedPattern {
    group: string[];
    message: string;
}

/**
 * Builds the `patterns` entries forbidding a runtime from importing packages of incompatible runtimes, each with a
 * tailored message.
 */
function crossRuntimePatterns(
    packageNamespace: string,
    self: RuntimeName,
    incompatible: readonly RuntimeName[],
): RestrictedPattern[] {
    return incompatible.flatMap((targetRuntime) =>
        RuntimePackageNamesRecord[targetRuntime].map((packageName) => {
            const specifier = namespaced(packageNamespace, packageName);

            return {
                group: [specifier, `${specifier}/**`],
                message: `A "${self}"-runtime module must not import "${specifier}", which targets the "${targetRuntime}" runtime. Move shared code into a "shared"/"common" package and import that from both.`,
            };
        }),
    );
}

/**
 * Generates the per-runtime overrides enforcing platform layering. One override is emitted for each browser-, node-,
 * and agnostic-runtime package name (matching the original ESLint config — worker files are a restricted _target_ but
 * have no override of their own).
 *
 * @param packageNamespace The namespace whose packages are subject to the rules, e.g. `@goauthentik`.
 *
 * @returns An array of oxlint `overrides` entries.
 */
export function createRuntimeOverrides(packageNamespace: string): OxlintOverride[] {
    const overrides: OxlintOverride[] = [];

    for (const packageName of RuntimePackageNamesRecord.browser) {
        overrides.push({
            files: createPackageFileMatcher(packageName),
            rules: {
                "no-restricted-imports": [
                    "warn",
                    {
                        paths: ambiguousNodeBuiltinPaths(),
                        patterns: crossRuntimePatterns(packageNamespace, "browser", [
                            "node",
                            "worker",
                        ]),
                    },
                ],
                "no-restricted-globals": restrictedBrowserGlobalsRule(),
            },
        });
    }

    for (const packageName of RuntimePackageNamesRecord.node) {
        overrides.push({
            files: createPackageFileMatcher(packageName),
            rules: {
                "no-restricted-imports": [
                    "warn",
                    {
                        paths: ambiguousNodeBuiltinPaths(),
                        patterns: crossRuntimePatterns(packageNamespace, "node", [
                            "browser",
                            "worker",
                        ]),
                    },
                ],
                "no-restricted-globals": restrictedBrowserGlobalsRule(),
            },
        });
    }

    for (const packageName of RuntimePackageNamesRecord.agnostic) {
        overrides.push({
            files: createPackageFileMatcher(packageName),
            rules: {
                "no-restricted-imports": [
                    "warn",
                    {
                        paths: allNodeBuiltinPaths(
                            `A "shared"/"common" module assumes no runtime and must not import Node built-ins.`,
                        ),
                        patterns: crossRuntimePatterns(packageNamespace, "agnostic", [
                            "browser",
                            "node",
                            "worker",
                        ]),
                    },
                ],
            },
        });
    }

    return overrides;
}

//#endregion
