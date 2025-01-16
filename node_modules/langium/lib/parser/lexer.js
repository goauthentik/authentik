/******************************************************************************
 * Copyright 2022 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import { Lexer as ChevrotainLexer } from 'chevrotain';
export class DefaultLexer {
    constructor(services) {
        const tokens = services.parser.TokenBuilder.buildTokens(services.Grammar, {
            caseInsensitive: services.LanguageMetaData.caseInsensitive
        });
        this.tokenTypes = this.toTokenTypeDictionary(tokens);
        const lexerTokens = isTokenTypeDictionary(tokens) ? Object.values(tokens) : tokens;
        this.chevrotainLexer = new ChevrotainLexer(lexerTokens, {
            positionTracking: 'full'
        });
    }
    get definition() {
        return this.tokenTypes;
    }
    tokenize(text) {
        var _a;
        const chevrotainResult = this.chevrotainLexer.tokenize(text);
        return {
            tokens: chevrotainResult.tokens,
            errors: chevrotainResult.errors,
            hidden: (_a = chevrotainResult.groups.hidden) !== null && _a !== void 0 ? _a : []
        };
    }
    toTokenTypeDictionary(buildTokens) {
        if (isTokenTypeDictionary(buildTokens))
            return buildTokens;
        const tokens = isIMultiModeLexerDefinition(buildTokens) ? Object.values(buildTokens.modes).flat() : buildTokens;
        const res = {};
        tokens.forEach(token => res[token.name] = token);
        return res;
    }
}
/**
 * Returns a check whether the given TokenVocabulary is TokenType array
 */
export function isTokenTypeArray(tokenVocabulary) {
    return Array.isArray(tokenVocabulary) && (tokenVocabulary.length === 0 || 'name' in tokenVocabulary[0]);
}
/**
 * Returns a check whether the given TokenVocabulary is IMultiModeLexerDefinition
 */
export function isIMultiModeLexerDefinition(tokenVocabulary) {
    return tokenVocabulary && 'modes' in tokenVocabulary && 'defaultMode' in tokenVocabulary;
}
/**
 * Returns a check whether the given TokenVocabulary is TokenTypeDictionary
 */
export function isTokenTypeDictionary(tokenVocabulary) {
    return !isTokenTypeArray(tokenVocabulary) && !isIMultiModeLexerDefinition(tokenVocabulary);
}
//# sourceMappingURL=lexer.js.map