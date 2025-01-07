/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { CustomPatternMatcherFunc, TokenPattern, TokenType, TokenVocabulary } from 'chevrotain';
import type { AbstractRule, Grammar, Keyword, TerminalRule } from '../languages/generated/ast.js';
import type { Stream } from '../utils/stream.js';
export interface TokenBuilderOptions {
    caseInsensitive?: boolean;
}
export interface TokenBuilder {
    buildTokens(grammar: Grammar, options?: TokenBuilderOptions): TokenVocabulary;
}
export declare class DefaultTokenBuilder implements TokenBuilder {
    buildTokens(grammar: Grammar, options?: TokenBuilderOptions): TokenVocabulary;
    protected buildTerminalTokens(rules: Stream<AbstractRule>): TokenType[];
    protected buildTerminalToken(terminal: TerminalRule): TokenType;
    protected requiresCustomPattern(regex: RegExp): boolean;
    protected regexPatternFunction(regex: RegExp): CustomPatternMatcherFunc;
    protected buildKeywordTokens(rules: Stream<AbstractRule>, terminalTokens: TokenType[], options?: TokenBuilderOptions): TokenType[];
    protected buildKeywordToken(keyword: Keyword, terminalTokens: TokenType[], caseInsensitive: boolean): TokenType;
    protected buildKeywordPattern(keyword: Keyword, caseInsensitive: boolean): TokenPattern;
    protected findLongerAlt(keyword: Keyword, terminalTokens: TokenType[]): TokenType[];
}
//# sourceMappingURL=token-builder.d.ts.map