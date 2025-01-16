/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { DSLMethodOpts, ILexingError, IOrAlt, IParserErrorMessageProvider, IRecognitionException, IToken, TokenType, TokenVocabulary } from 'chevrotain';
import type { AbstractElement, Action, ParserRule } from '../languages/generated/ast.js';
import type { LangiumCoreServices } from '../services.js';
import type { AstNode } from '../syntax-tree.js';
import type { Lexer } from './lexer.js';
import type { IParserConfig } from './parser-config.js';
import { EmbeddedActionsParser } from 'chevrotain';
export type ParseResult<T = AstNode> = {
    value: T;
    parserErrors: IRecognitionException[];
    lexerErrors: ILexingError[];
};
export declare const DatatypeSymbol: unique symbol;
type RuleResult = (args: Args) => any;
type Args = Record<string, boolean>;
type RuleImpl = (args: Args) => any;
export interface BaseParser {
    rule(rule: ParserRule, impl: RuleImpl): RuleResult;
    alternatives(idx: number, choices: Array<IOrAlt<any>>): void;
    optional(idx: number, callback: DSLMethodOpts<unknown>): void;
    many(idx: number, callback: DSLMethodOpts<unknown>): void;
    atLeastOne(idx: number, callback: DSLMethodOpts<unknown>): void;
    consume(idx: number, tokenType: TokenType, feature: AbstractElement): void;
    subrule(idx: number, rule: RuleResult, feature: AbstractElement, args: Args): void;
    action($type: string, action: Action): void;
    construct(): unknown;
    isRecording(): boolean;
    get unorderedGroups(): Map<string, boolean[]>;
    getRuleStack(): number[];
}
export declare abstract class AbstractLangiumParser implements BaseParser {
    protected readonly lexer: Lexer;
    protected readonly wrapper: ChevrotainWrapper;
    protected _unorderedGroups: Map<string, boolean[]>;
    constructor(services: LangiumCoreServices);
    alternatives(idx: number, choices: Array<IOrAlt<any>>): void;
    optional(idx: number, callback: DSLMethodOpts<unknown>): void;
    many(idx: number, callback: DSLMethodOpts<unknown>): void;
    atLeastOne(idx: number, callback: DSLMethodOpts<unknown>): void;
    abstract rule(rule: ParserRule, impl: RuleImpl): RuleResult;
    abstract consume(idx: number, tokenType: TokenType, feature: AbstractElement): void;
    abstract subrule(idx: number, rule: RuleResult, feature: AbstractElement, args: Args): void;
    abstract action($type: string, action: Action): void;
    abstract construct(): unknown;
    isRecording(): boolean;
    get unorderedGroups(): Map<string, boolean[]>;
    getRuleStack(): number[];
    finalize(): void;
}
export declare class LangiumParser extends AbstractLangiumParser {
    private readonly linker;
    private readonly converter;
    private readonly astReflection;
    private readonly nodeBuilder;
    private stack;
    private mainRule;
    private assignmentMap;
    private get current();
    constructor(services: LangiumCoreServices);
    rule(rule: ParserRule, impl: RuleImpl): RuleResult;
    parse<T extends AstNode = AstNode>(input: string): ParseResult<T>;
    private startImplementation;
    consume(idx: number, tokenType: TokenType, feature: AbstractElement): void;
    /**
     * Most consumed parser tokens are valid. However there are two cases in which they are not valid:
     *
     * 1. They were inserted during error recovery by the parser. These tokens don't really exist and should not be further processed
     * 2. They contain invalid token ranges. This might include the special EOF token, or other tokens produced by invalid token builders.
     */
    private isValidToken;
    subrule(idx: number, rule: RuleResult, feature: AbstractElement, args: Args): void;
    private performSubruleAssignment;
    action($type: string, action: Action): void;
    construct(pop?: boolean): unknown;
    private getAssignment;
    private assign;
    private assignWithoutOverride;
    get definitionErrors(): IParserDefinitionError[];
}
export interface IParserDefinitionError {
    message: string;
    type: number;
    ruleName?: string;
}
export declare abstract class AbstractParserErrorMessageProvider implements IParserErrorMessageProvider {
    buildMismatchTokenMessage(options: {
        expected: TokenType;
        actual: IToken;
        previous: IToken;
        ruleName: string;
    }): string;
    buildNotAllInputParsedMessage(options: {
        firstRedundant: IToken;
        ruleName: string;
    }): string;
    buildNoViableAltMessage(options: {
        expectedPathsPerAlt: TokenType[][][];
        actual: IToken[];
        previous: IToken;
        customUserDescription: string;
        ruleName: string;
    }): string;
    buildEarlyExitMessage(options: {
        expectedIterationPaths: TokenType[][];
        actual: IToken[];
        previous: IToken;
        customUserDescription: string;
        ruleName: string;
    }): string;
}
export declare class LangiumParserErrorMessageProvider extends AbstractParserErrorMessageProvider {
    buildMismatchTokenMessage({ expected, actual }: {
        expected: TokenType;
        actual: IToken;
        previous: IToken;
        ruleName: string;
    }): string;
    buildNotAllInputParsedMessage({ firstRedundant }: {
        firstRedundant: IToken;
        ruleName: string;
    }): string;
}
export interface CompletionParserResult {
    tokens: IToken[];
    elementStack: AbstractElement[];
    tokenIndex: number;
}
export declare class LangiumCompletionParser extends AbstractLangiumParser {
    private mainRule;
    private tokens;
    private elementStack;
    private lastElementStack;
    private nextTokenIndex;
    private stackSize;
    action(): void;
    construct(): unknown;
    parse(input: string): CompletionParserResult;
    rule(rule: ParserRule, impl: RuleImpl): RuleResult;
    private resetState;
    private startImplementation;
    private removeUnexpectedElements;
    keepStackSize(): number;
    resetStackSize(size: number): void;
    consume(idx: number, tokenType: TokenType, feature: AbstractElement): void;
    subrule(idx: number, rule: RuleResult, feature: AbstractElement, args: Args): void;
    before(element: AbstractElement): void;
    after(element: AbstractElement): void;
    get currIdx(): number;
}
/**
 * This class wraps the embedded actions parser of chevrotain and exposes protected methods.
 * This way, we can build the `LangiumParser` as a composition.
 */
declare class ChevrotainWrapper extends EmbeddedActionsParser {
    definitionErrors: IParserDefinitionError[];
    constructor(tokens: TokenVocabulary, config?: IParserConfig);
    get IS_RECORDING(): boolean;
    DEFINE_RULE(name: string, impl: RuleImpl): RuleResult;
    wrapSelfAnalysis(): void;
    wrapConsume(idx: number, tokenType: TokenType): IToken;
    wrapSubrule(idx: number, rule: RuleResult, args: Args): unknown;
    wrapOr(idx: number, choices: Array<IOrAlt<any>>): void;
    wrapOption(idx: number, callback: DSLMethodOpts<unknown>): void;
    wrapMany(idx: number, callback: DSLMethodOpts<unknown>): void;
    wrapAtLeastOne(idx: number, callback: DSLMethodOpts<unknown>): void;
}
export {};
//# sourceMappingURL=langium-parser.d.ts.map