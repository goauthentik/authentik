/**
 * @file Vendored Lexer Implementation
 *
 * @license MIT
 * @author Aadit M Shah <aaditmshah@fastmail.fm>
 * @see https://github.com/aaditmshah/lexer/tree/master
 */

/**
 * @typedef {(this: Lexer, chr: string) => any} DefunctFunction
 */

/**
 * @typedef {(this: Lexer, ...args: RegExpExecArray) => string | string[] | undefined} RuleAction
 */

/**
 * @typedef {Object} Rule
 * @property {RegExp} pattern
 * @property {boolean} global
 * @property {RuleAction} action
 * @property {number[]} start
 */

/**
 * @typedef {Object} Match
 * @property {RegExpExecArray} result
 * @property {RuleAction} action
 * @property {number} length
 */

/**
 * Lexer class for tokenizing input strings.
 */
export class Lexer {
    /**
     * @type {string[]}
     */
    tokens = [];
    /**
     * @type {Rule[]}
     */
    rules = [];
    /**
     * @type {number}
     */
    remove = 0;
    /**
     * @type {number}
     */
    state = 0;
    /**
     * @type {number}
     */
    index = 0;
    /**
     * @type {string}
     */
    input = "";

    /**
     * @param {DefunctFunction} [defunct]
     */
    constructor(defunct) {
        defunct ||= function (chr) {
            throw new Error("Unexpected character at index " + (this.index - 1) + ": " + chr);
        };

        this.defunct = defunct;
    }

    /**
     * Add a lexing rule.
     *
     * @param {RegExp} pattern
     * @param {RuleAction} action
     * @param {number[]} [start]
     * @returns {Lexer}
     */
    addRule = (pattern, action, start) => {
        const global = pattern.global;

        if (!global || !pattern.sticky) {
            let flags = "gy";

            if (pattern.multiline) flags += "m";
            if (pattern.ignoreCase) flags += "i";
            if (pattern.unicode) flags += "u";
            pattern = new RegExp(pattern.source, flags);
        }

        if (!Array.isArray(start)) start = [0];

        this.rules.push({
            pattern: pattern,
            global: global,
            action: action,
            start: start,
        });

        return this;
    };

    /**
     * Set the input string for lexing.
     *
     * @param {string} input
     * @returns {Lexer}
     */
    setInput = (input) => {
        this.remove = 0;
        this.state = 0;
        this.index = 0;
        this.tokens.length = 0;
        this.input = input;
        return this;
    };

    /**
     * Lex the next token from the input.
     *
     * @returns {string | string[] | undefined}
     */
    lex = () => {
        if (this.tokens.length) return this.tokens.shift();

        this.reject = true;

        while (this.index <= this.input.length) {
            const matches = this.scan().splice(this.remove);
            const index = this.index;

            while (matches.length) {
                if (!this.reject) {
                    break;
                }
                const match = matches.shift();

                if (!match) break;

                const result = match.result;
                const length = match.length;
                this.index += length;
                this.reject = false;
                this.remove++;

                let token = match.action.apply(this, result);

                if (this.reject) {
                    this.index = result.index;
                } else if (Array.isArray(token)) {
                    this.tokens = token.slice(1);
                    token = token[0];
                } else {
                    if (length) this.remove = 0;
                    return token;
                }
            }

            const input = this.input;

            if (index < input.length) {
                if (this.reject) {
                    this.remove = 0;
                    const token = this.defunct(input.charAt(this.index++));
                    if (typeof token !== "undefined") {
                        if (Array.isArray(token)) {
                            this.tokens = token.slice(1);
                            return token[0];
                        }

                        return token;
                    }
                } else {
                    if (this.index !== index) this.remove = 0;
                    this.reject = true;
                }
            } else if (matches.length) this.reject = true;
            else break;
        }
    };

    /**
     * Scan the input for matches.
     *
     * @returns {Match[]}
     */
    scan = () => {
        /**
         * @type {Match[]}
         */
        const matches = [];
        let index = 0;

        const state = this.state;
        const lastIndex = this.index;
        const input = this.input;

        for (let i = 0, length = this.rules.length; i < length; i++) {
            const rule = this.rules[i];
            const start = rule.start;
            const states = start.length;

            if (!states || start.indexOf(state) >= 0 || (state % 2 && states === 1 && !start[0])) {
                const pattern = rule.pattern;
                pattern.lastIndex = lastIndex;
                const result = pattern.exec(input);

                if (!result || result.index !== lastIndex) {
                    continue;
                }

                let j = matches.push({
                    result: result,
                    action: rule.action,
                    length: result[0].length,
                });

                if (rule.global) {
                    index = j;
                }

                while (--j > index) {
                    const k = j - 1;

                    if (matches[j].length > matches[k].length) {
                        const temple = matches[j];
                        matches[j] = matches[k];
                        matches[k] = temple;
                    }
                }
            }
        }

        return matches;
    };
}

export default Lexer;
