/******************************************************************************
 * Copyright 2022 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { ILexingError, IMultiModeLexerDefinition, IToken, TokenType, TokenTypeDictionary, TokenVocabulary } from 'chevrotain';
import type { LangiumCoreServices } from '../services.js';
import { Lexer as ChevrotainLexer } from 'chevrotain';
export interface LexerResult {
    /**
     * A list of all tokens that were lexed from the input.
     *
     * Note that Langium requires the optional properties
     * `startLine`, `startColumn`, `endOffset`, `endLine` and `endColumn` to be set on each token.
     */
    tokens: IToken[];
    /**
     * Contains hidden tokens, usually comments.
     */
    hidden: IToken[];
    errors: ILexingError[];
}
export interface Lexer {
    readonly definition: TokenTypeDictionary;
    tokenize(text: string): LexerResult;
}
export declare class DefaultLexer implements Lexer {
    protected chevrotainLexer: ChevrotainLexer;
    protected tokenTypes: TokenTypeDictionary;
    constructor(services: LangiumCoreServices);
    get definition(): TokenTypeDictionary;
    tokenize(text: string): LexerResult;
    protected toTokenTypeDictionary(buildTokens: TokenVocabulary): TokenTypeDictionary;
}
/**
 * Returns a check whether the given TokenVocabulary is TokenType array
 */
export declare function isTokenTypeArray(tokenVocabulary: TokenVocabulary): tokenVocabulary is TokenType[];
/**
 * Returns a check whether the given TokenVocabulary is IMultiModeLexerDefinition
 */
export declare function isIMultiModeLexerDefinition(tokenVocabulary: TokenVocabulary): tokenVocabulary is IMultiModeLexerDefinition;
/**
 * Returns a check whether the given TokenVocabulary is TokenTypeDictionary
 */
export declare function isTokenTypeDictionary(tokenVocabulary: TokenVocabulary): tokenVocabulary is TokenTypeDictionary;
//# sourceMappingURL=lexer.d.ts.map