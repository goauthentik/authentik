/**
 * @file Vendored Lexer Implementation
 *
 * @license MIT
 * @author Aadit M Shah <aaditmshah@fastmail.fm>
 * @see https://github.com/aaditmshah/lexer/tree/master
 */

/**
 * A token produced by a {@link LexerAction}. The lexer is agnostic to the
 * concrete token shape; consumers pick whatever representation suits them.
 *
 * @typedef {unknown} Token
 */

/**
 * A rule action. Invoked with the regex match (full match followed by capture
 * groups) bound to the owning {@link Lexer} so it can read or set `state`,
 * `index`, and `reject`.
 *
 * Return values:
 * - `null` (or `undefined` from an implicit return) — discard the match and continue scanning.
 * - a single token — yield it from {@link Lexer.lex}.
 * - an array of tokens — yield the first; queue the rest for subsequent calls.
 *
 * @callback LexerAction
 * @this {Lexer}
 * @param {...string[]} match
 * @returns {Token | Token[] | null | void}
 */

/**
 * @typedef {object} LexerRule
 * @property {RegExp} pattern Sticky-compiled pattern used to probe the input.
 * @property {boolean} global Whether the user-supplied pattern was global.
 * @property {LexerAction} action
 * @property {number[]} start States in which the rule is active. `[0]` is the default state; an empty array means "any state".
 */

/**
 * @typedef {object} LexerMatch
 * @property {RegExpExecArray} result
 * @property {LexerAction} action
 * @property {number} length
 * @property {boolean} global Whether the producing rule was declared with the `g` flag.
 */

/**
 * Handler invoked when no rule matches at the current position.
 *
 * @callback DefunctHandler
 * @this {Lexer}
 * @param {string} chr The unexpected character.
 * @returns {Token | Token[] | null | void}
 */

/**
 * @type {DefunctHandler}
 */
function defaultDefunct(chr) {
    throw new Error(`Unexpected character at index ${this.index - 1}: ${chr}`);
}

/**
 * Lexer class for tokenizing input strings.
 */
export class Lexer {
    /**
     * Current lexer state. Rules whose `start` array contains this value (or
     * is empty) are eligible to match. Odd-numbered states are also matched
     * by rules declared with `start: [0]`, mirroring flex's inclusive states.
     *
     * @type {number}
     */
    state = 0;

    /** @type {number} */
    index = 0;

    /** @type {string} */
    input = "";

    /**
     * When set to `true` from inside an action, the current match is rolled
     * back and the next-best match is tried instead.
     *
     * @type {boolean}
     */
    reject = false;

    /** @type {LexerRule[]} */
    #rules = [];

    /** @type {Token[]} */
    #tokens = [];

    /** @type {number} */
    #remove = 0;

    /** @type {DefunctHandler} */
    #defunct;

    /**
     * @param {DefunctHandler} [defunct] Optional handler for unexpected characters.
     */
    constructor(defunct) {
        this.#defunct = typeof defunct === "function" ? defunct : defaultDefunct;
    }

    /**
     * Register a tokenization rule.
     *
     * @param {RegExp} pattern
     * @param {LexerAction} action
     * @param {number[]} [start] States in which the rule is active. Defaults to `[0]`.
     * @returns {this}
     */
    addRule(pattern, action, start) {
        const global = pattern.global;

        if (!global || !pattern.sticky) {
            let flags = "gy";
            if (pattern.multiline) flags += "m";
            if (pattern.ignoreCase) flags += "i";
            if (pattern.unicode) flags += "u";
            pattern = new RegExp(pattern.source, flags);
        }

        this.#rules.push({
            pattern,
            global,
            action,
            start: Array.isArray(start) ? start : [0],
        });

        return this;
    }

    /**
     * Reset the lexer and load a new input string.
     *
     * @param {string} input
     * @returns {this}
     */
    setInput(input) {
        this.#remove = 0;
        this.state = 0;
        this.index = 0;
        this.#tokens.length = 0;
        this.input = input;
        return this;
    }

    /**
     * Produce the next token from the input, or `null` once exhausted.
     *
     * @returns {Token | null}
     */
    lex() {
        if (this.#tokens.length) return /** @type {Token} */ (this.#tokens.shift());

        this.reject = true;

        while (this.index <= this.input.length) {
            const matches = this.#scan().splice(this.#remove);
            const index = this.index;

            while (matches.length) {
                if (!this.reject) break;

                const match = /** @type {LexerMatch} */ (matches.shift());
                const { result, length } = match;
                this.index += length;
                this.reject = false;
                this.#remove++;

                let token = match.action.apply(
                    this,
                    /** @type {string[]} */ (/** @type {unknown} */ (result)),
                );

                if (this.reject) {
                    this.index = result.index;
                } else if (token !== null && token !== undefined) {
                    if (Array.isArray(token)) {
                        this.#tokens = token.slice(1);
                        token = token[0];
                    }
                    if (length) this.#remove = 0;
                    return token;
                }
            }

            const input = this.input;

            if (index < input.length) {
                if (this.reject) {
                    this.#remove = 0;
                    const token = this.#defunct(input.charAt(this.index++));
                    if (token !== null && token !== undefined) {
                        if (Array.isArray(token)) {
                            this.#tokens = token.slice(1);
                            return token[0];
                        }
                        return token;
                    }
                } else {
                    if (this.index !== index) this.#remove = 0;
                    this.reject = true;
                }
            } else if (matches.length) {
                this.reject = true;
            } else {
                break;
            }
        }

        return null;
    }

    /**
     * Probe every state-eligible rule at the current position, returning the
     * matches sorted by length (longest first), with global rules pinned
     * after non-global ones to preserve flex's "longest non-global wins"
     * tie-breaking.
     *
     * @returns {LexerMatch[]}
     */
    #scan() {
        /** @type {LexerMatch[]} */
        const matches = [];

        const state = this.state;
        const lastIndex = this.index;
        const input = this.input;

        for (const rule of this.#rules) {
            const start = rule.start;
            const states = start.length;
            const eligible =
                !states || start.indexOf(state) >= 0 || (state % 2 && states === 1 && !start[0]);

            if (!eligible) continue;

            const pattern = rule.pattern;
            pattern.lastIndex = lastIndex;
            const result = pattern.exec(input);

            if (!result || result.index !== lastIndex) continue;

            let j = matches.push({
                result,
                action: rule.action,
                length: result[0].length,
                global: rule.global,
            });

            while (--j > 0) {
                const k = j - 1;
                const cur = matches[j];
                const prev = matches[k];
                const longer = cur.length > prev.length;
                const tieFavorsCur = cur.length === prev.length && prev.global && !cur.global;

                if (!longer && !tieFavorsCur) break;

                matches[j] = prev;
                matches[k] = cur;
            }
        }

        return matches;
    }
}

export default Lexer;
