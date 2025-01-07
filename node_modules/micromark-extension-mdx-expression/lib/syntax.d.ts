/**
 * Create an extension for `micromark` to enable MDX expression syntax.
 *
 * @param {Options | null | undefined} [options]
 *   Configuration (optional).
 * @returns {Extension}
 *   Extension for `micromark` that can be passed in `extensions` to enable MDX
 *   expression syntax.
 */
export function mdxExpression(options?: Options | null | undefined): Extension;
export type Acorn = import('micromark-util-events-to-acorn').Acorn;
export type AcornOptions = import('micromark-util-events-to-acorn').AcornOptions;
export type Extension = import('micromark-util-types').Extension;
export type State = import('micromark-util-types').State;
export type TokenizeContext = import('micromark-util-types').TokenizeContext;
export type Tokenizer = import('micromark-util-types').Tokenizer;
/**
 * Configuration (optional).
 */
export type Options = {
    /**
     * Acorn parser to use (optional).
     */
    acorn?: Acorn | null | undefined;
    /**
     * Configuration for acorn (default: `{ecmaVersion: 2024, locations: true,
     * sourceType: 'module'}`).
     *
     * All fields except `locations` can be set.
     */
    acornOptions?: AcornOptions | null | undefined;
    /**
     * Whether to add `estree` fields to tokens with results from acorn (default:
     * `false`).
     */
    addResult?: boolean | null | undefined;
    /**
     * Undocumented option to parse only a spread (used by
     * `micromark-extension-mdx-jsx` to parse spread attributes) (default:
     * `false`).
     */
    spread?: boolean | null | undefined;
    /**
     * Undocumented option to disallow empty attributes (used by
     * `micromark-extension-mdx-jsx` to prohobit empty attribute values)
     * (default: `false`).
     */
    allowEmpty?: boolean | null | undefined;
};
