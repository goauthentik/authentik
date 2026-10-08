/**
 * @remarks
 *   Kept beside the rules rather than inline in the factory so the set has one home: a rule added
 *   to `./plugin.ts` and forgotten here is silently unreachable, which is how `padding-lines` first
 *   shipped enabled in the config while commented out of the plugin.
 * @file The rule entries for the bundled blank-line padding rules.
 */

/** The `goauthentik/*` padding rules, enabled together by `createOxlintConfig({ padding: true })`. */
export const PaddingRules: Record<string, string> = {
    "goauthentik/padding-lines": "warn",
    "goauthentik/console-padding": "warn",
    "goauthentik/multiline-statement-padding": "warn",
};
