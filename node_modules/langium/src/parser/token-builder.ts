/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/

import type { CustomPatternMatcherFunc, TokenPattern, TokenType, TokenVocabulary } from 'chevrotain';
import type { AbstractRule, Grammar, Keyword, TerminalRule } from '../languages/generated/ast.js';
import type { Stream } from '../utils/stream.js';
import { Lexer } from 'chevrotain';
import { isKeyword, isParserRule, isTerminalRule } from '../languages/generated/ast.js';
import { streamAllContents } from '../utils/ast-utils.js';
import { getAllReachableRules, terminalRegex } from '../utils/grammar-utils.js';
import { getCaseInsensitivePattern, isWhitespace, partialMatches } from '../utils/regexp-utils.js';
import { stream } from '../utils/stream.js';

export interface TokenBuilderOptions {
    caseInsensitive?: boolean
}

export interface TokenBuilder {
    buildTokens(grammar: Grammar, options?: TokenBuilderOptions): TokenVocabulary;
}

export class DefaultTokenBuilder implements TokenBuilder {

    buildTokens(grammar: Grammar, options?: TokenBuilderOptions): TokenVocabulary {
        const reachableRules = stream(getAllReachableRules(grammar, false));
        const terminalTokens: TokenType[] = this.buildTerminalTokens(reachableRules);
        const tokens: TokenType[] = this.buildKeywordTokens(reachableRules, terminalTokens, options);

        terminalTokens.forEach(terminalToken => {
            const pattern = terminalToken.PATTERN;
            if (typeof pattern === 'object' && pattern && 'test' in pattern && isWhitespace(pattern)) {
                tokens.unshift(terminalToken);
            } else {
                tokens.push(terminalToken);
            }
        });
        // We don't need to add the EOF token explicitly.
        // It is automatically available at the end of the token stream.
        return tokens;
    }

    protected buildTerminalTokens(rules: Stream<AbstractRule>): TokenType[] {
        return rules.filter(isTerminalRule).filter(e => !e.fragment)
            .map(terminal => this.buildTerminalToken(terminal)).toArray();
    }

    protected buildTerminalToken(terminal: TerminalRule): TokenType {
        const regex = terminalRegex(terminal);
        const pattern = this.requiresCustomPattern(regex) ? this.regexPatternFunction(regex) : regex;
        const tokenType: TokenType = {
            name: terminal.name,
            PATTERN: pattern,
            LINE_BREAKS: true
        };
        if (terminal.hidden) {
            // Only skip tokens that are able to accept whitespace
            tokenType.GROUP = isWhitespace(regex) ? Lexer.SKIPPED : 'hidden';
        }
        return tokenType;
    }

    protected requiresCustomPattern(regex: RegExp): boolean {
        if (regex.flags.includes('u')) {
            // Unicode regexes are not supported by Chevrotain.
            return true;
        } else if (regex.source.includes('?<=') || regex.source.includes('?<!')) {
            // Negative and positive lookbehind are not supported by Chevrotain yet.
            return true;
        } else {
            return false;
        }
    }

    protected regexPatternFunction(regex: RegExp): CustomPatternMatcherFunc {
        const stickyRegex = new RegExp(regex, regex.flags + 'y');
        return (text, offset) => {
            stickyRegex.lastIndex = offset;
            const execResult = stickyRegex.exec(text);
            return execResult;
        };
    }

    protected buildKeywordTokens(rules: Stream<AbstractRule>, terminalTokens: TokenType[], options?: TokenBuilderOptions): TokenType[] {
        return rules
            // We filter by parser rules, since keywords in terminal rules get transformed into regex and are not actual tokens
            .filter(isParserRule)
            .flatMap(rule => streamAllContents(rule).filter(isKeyword))
            .distinct(e => e.value).toArray()
            // Sort keywords by descending length
            .sort((a, b) => b.value.length - a.value.length)
            .map(keyword => this.buildKeywordToken(keyword, terminalTokens, Boolean(options?.caseInsensitive)));
    }

    protected buildKeywordToken(keyword: Keyword, terminalTokens: TokenType[], caseInsensitive: boolean): TokenType {
        return {
            name: keyword.value,
            PATTERN: this.buildKeywordPattern(keyword, caseInsensitive),
            LONGER_ALT: this.findLongerAlt(keyword, terminalTokens)
        };
    }

    protected buildKeywordPattern(keyword: Keyword, caseInsensitive: boolean): TokenPattern {
        return caseInsensitive ?
            new RegExp(getCaseInsensitivePattern(keyword.value)) :
            keyword.value;
    }

    protected findLongerAlt(keyword: Keyword, terminalTokens: TokenType[]): TokenType[] {
        return terminalTokens.reduce((longerAlts: TokenType[], token) => {
            const pattern = token?.PATTERN as RegExp;
            if (pattern?.source && partialMatches('^' + pattern.source + '$', keyword.value)) {
                longerAlts.push(token);
            }
            return longerAlts;
        }, []);
    }
}
