/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/

/* eslint-disable @typescript-eslint/no-explicit-any */
import type { DSLMethodOpts, ILexingError, IOrAlt, IParserErrorMessageProvider, IRecognitionException, IToken, TokenType, TokenVocabulary } from 'chevrotain';
import type { AbstractElement, Action, Assignment, ParserRule } from '../languages/generated/ast.js';
import type { Linker } from '../references/linker.js';
import type { LangiumCoreServices } from '../services.js';
import type { AstNode, AstReflection, CompositeCstNode, CstNode } from '../syntax-tree.js';
import type { Lexer } from './lexer.js';
import type { IParserConfig } from './parser-config.js';
import type { ValueConverter } from './value-converter.js';
import { defaultParserErrorProvider, EmbeddedActionsParser, LLkLookaheadStrategy } from 'chevrotain';
import { LLStarLookaheadStrategy } from 'chevrotain-allstar';
import { isAssignment, isCrossReference, isKeyword } from '../languages/generated/ast.js';
import { getTypeName, isDataTypeRule } from '../utils/grammar-utils.js';
import { assignMandatoryProperties, getContainerOfType, linkContentToContainer } from '../utils/ast-utils.js';
import { CstNodeBuilder } from './cst-node-builder.js';

export type ParseResult<T = AstNode> = {
    value: T,
    parserErrors: IRecognitionException[],
    lexerErrors: ILexingError[]
}

export const DatatypeSymbol = Symbol('Datatype');

interface DataTypeNode {
    $cstNode: CompositeCstNode
    /** Instead of a string, this node is uniquely identified by the `Datatype` symbol */
    $type: symbol
    /** Used as a storage for all parsed terminals, keywords and sub-datatype rules */
    value: string
}

function isDataTypeNode(node: { $type: string | symbol | undefined }): node is DataTypeNode {
    return node.$type === DatatypeSymbol;
}

type RuleResult = (args: Args) => any;

type Args = Record<string, boolean>;

type RuleImpl = (args: Args) => any;

interface AssignmentElement {
    assignment?: Assignment
    isCrossRef: boolean
}

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

const ruleSuffix = '\u200B';
const withRuleSuffix = (name: string): string => name.endsWith(ruleSuffix) ? name : name + ruleSuffix;

export abstract class AbstractLangiumParser implements BaseParser {

    protected readonly lexer: Lexer;
    protected readonly wrapper: ChevrotainWrapper;
    protected _unorderedGroups: Map<string, boolean[]> = new Map<string, boolean[]>();

    constructor(services: LangiumCoreServices) {
        this.lexer = services.parser.Lexer;
        const tokens = this.lexer.definition;
        this.wrapper = new ChevrotainWrapper(tokens, {
            ...services.parser.ParserConfig,
            errorMessageProvider: services.parser.ParserErrorMessageProvider
        });
    }

    alternatives(idx: number, choices: Array<IOrAlt<any>>): void {
        this.wrapper.wrapOr(idx, choices);
    }

    optional(idx: number, callback: DSLMethodOpts<unknown>): void {
        this.wrapper.wrapOption(idx, callback);
    }

    many(idx: number, callback: DSLMethodOpts<unknown>): void {
        this.wrapper.wrapMany(idx, callback);
    }

    atLeastOne(idx: number, callback: DSLMethodOpts<unknown>): void {
        this.wrapper.wrapAtLeastOne(idx, callback);
    }

    abstract rule(rule: ParserRule, impl: RuleImpl): RuleResult;
    abstract consume(idx: number, tokenType: TokenType, feature: AbstractElement): void;
    abstract subrule(idx: number, rule: RuleResult, feature: AbstractElement, args: Args): void;
    abstract action($type: string, action: Action): void;
    abstract construct(): unknown;

    isRecording(): boolean {
        return this.wrapper.IS_RECORDING;
    }

    get unorderedGroups(): Map<string, boolean[]> {
        return this._unorderedGroups;
    }

    getRuleStack(): number[] {
        return (this.wrapper as any).RULE_STACK;
    }

    finalize(): void {
        this.wrapper.wrapSelfAnalysis();
    }
}

export class LangiumParser extends AbstractLangiumParser {
    private readonly linker: Linker;
    private readonly converter: ValueConverter;
    private readonly astReflection: AstReflection;
    private readonly nodeBuilder = new CstNodeBuilder();
    private stack: any[] = [];
    private mainRule!: RuleResult;
    private assignmentMap = new Map<AbstractElement, AssignmentElement | undefined>();

    private get current(): any {
        return this.stack[this.stack.length - 1];
    }

    constructor(services: LangiumCoreServices) {
        super(services);
        this.linker = services.references.Linker;
        this.converter = services.parser.ValueConverter;
        this.astReflection = services.shared.AstReflection;
    }

    rule(rule: ParserRule, impl: RuleImpl): RuleResult {
        const type = rule.fragment ? undefined : isDataTypeRule(rule) ? DatatypeSymbol : getTypeName(rule);
        const ruleMethod = this.wrapper.DEFINE_RULE(withRuleSuffix(rule.name), this.startImplementation(type, impl).bind(this));
        if (rule.entry) {
            this.mainRule = ruleMethod;
        }
        return ruleMethod;
    }

    parse<T extends AstNode = AstNode>(input: string): ParseResult<T> {
        this.nodeBuilder.buildRootNode(input);
        const lexerResult = this.lexer.tokenize(input);
        this.wrapper.input = lexerResult.tokens;
        const result = this.mainRule.call(this.wrapper, {});
        this.nodeBuilder.addHiddenTokens(lexerResult.hidden);
        this.unorderedGroups.clear();
        return {
            value: result,
            lexerErrors: lexerResult.errors,
            parserErrors: this.wrapper.errors
        };
    }

    private startImplementation($type: string | symbol | undefined, implementation: RuleImpl): RuleImpl {
        return (args) => {
            if (!this.isRecording()) {
                const node: any = { $type };
                this.stack.push(node);
                if ($type === DatatypeSymbol) {
                    node.value = '';
                }
            }
            let result: unknown;
            try {
                result = implementation(args);
            } catch (err) {
                result = undefined;
            }
            if (!this.isRecording() && result === undefined) {
                result = this.construct();
            }
            return result;
        };
    }

    consume(idx: number, tokenType: TokenType, feature: AbstractElement): void {
        const token = this.wrapper.wrapConsume(idx, tokenType);
        if (!this.isRecording() && this.isValidToken(token)) {
            const leafNode = this.nodeBuilder.buildLeafNode(token, feature);
            const { assignment, isCrossRef } = this.getAssignment(feature);
            const current = this.current;
            if (assignment) {
                const convertedValue = isKeyword(feature) ? token.image : this.converter.convert(token.image, leafNode);
                this.assign(assignment.operator, assignment.feature, convertedValue, leafNode, isCrossRef);
            } else if (isDataTypeNode(current)) {
                let text = token.image;
                if (!isKeyword(feature)) {
                    text = this.converter.convert(text, leafNode).toString();
                }
                current.value += text;
            }
        }
    }

    /**
     * Most consumed parser tokens are valid. However there are two cases in which they are not valid:
     *
     * 1. They were inserted during error recovery by the parser. These tokens don't really exist and should not be further processed
     * 2. They contain invalid token ranges. This might include the special EOF token, or other tokens produced by invalid token builders.
     */
    private isValidToken(token: IToken): boolean {
        return !token.isInsertedInRecovery && !isNaN(token.startOffset) && typeof token.endOffset === 'number' && !isNaN(token.endOffset);
    }

    subrule(idx: number, rule: RuleResult, feature: AbstractElement, args: Args): void {
        let cstNode: CompositeCstNode | undefined;
        if (!this.isRecording()) {
            cstNode = this.nodeBuilder.buildCompositeNode(feature);
        }
        const subruleResult = this.wrapper.wrapSubrule(idx, rule, args) as any;
        if (!this.isRecording() && cstNode && cstNode.length > 0) {
            this.performSubruleAssignment(subruleResult, feature, cstNode);
        }
    }

    private performSubruleAssignment(result: any, feature: AbstractElement, cstNode: CompositeCstNode): void {
        const { assignment, isCrossRef } = this.getAssignment(feature);
        if (assignment) {
            this.assign(assignment.operator, assignment.feature, result, cstNode, isCrossRef);
        } else if (!assignment) {
            // If we call a subrule without an assignment we either:
            // 1. append the result of the subrule (data type rule)
            // 2. override the current object with the newly parsed object
            // If the current element is an AST node and the result of the subrule
            // is a data type rule, we can safely discard the results.
            const current = this.current;
            if (isDataTypeNode(current)) {
                current.value += result.toString();
            } else if (typeof result === 'object' && result) {
                const resultKind = result.$type;
                const object = this.assignWithoutOverride(result, current);
                if (resultKind) {
                    object.$type = resultKind;
                }
                const newItem = object;
                this.stack.pop();
                this.stack.push(newItem);
            }
        }
    }

    action($type: string, action: Action): void {
        if (!this.isRecording()) {
            let last = this.current;
            // This branch is used for left recursive grammar rules.
            // Those don't call `construct` before another action.
            // Therefore, we need to call it here.
            if (!last.$cstNode && action.feature && action.operator) {
                last = this.construct(false);
                const feature = last.$cstNode.feature;
                this.nodeBuilder.buildCompositeNode(feature);
            }
            const newItem = { $type };
            this.stack.pop();
            this.stack.push(newItem);
            if (action.feature && action.operator) {
                this.assign(action.operator, action.feature, last, last.$cstNode, false);
            }
        }
    }

    construct(pop = true): unknown {
        if (this.isRecording()) {
            return undefined;
        }
        const obj = this.current;
        linkContentToContainer(obj);
        this.nodeBuilder.construct(obj);
        if (pop) {
            this.stack.pop();
        }
        if (isDataTypeNode(obj)) {
            return this.converter.convert(obj.value, obj.$cstNode);
        } else {
            assignMandatoryProperties(this.astReflection, obj);
        }
        return obj;
    }

    private getAssignment(feature: AbstractElement): AssignmentElement {
        if (!this.assignmentMap.has(feature)) {
            const assignment = getContainerOfType(feature, isAssignment);
            this.assignmentMap.set(feature, {
                assignment: assignment,
                isCrossRef: assignment ? isCrossReference(assignment.terminal) : false
            });
        }
        return this.assignmentMap.get(feature)!;
    }

    private assign(operator: string, feature: string, value: unknown, cstNode: CstNode, isCrossRef: boolean): void {
        const obj = this.current;
        let item: unknown;
        if (isCrossRef && typeof value === 'string') {
            item = this.linker.buildReference(obj, feature, cstNode, value);
        } else {
            item = value;
        }
        switch (operator) {
            case '=': {
                obj[feature] = item;
                break;
            }
            case '?=': {
                obj[feature] = true;
                break;
            }
            case '+=': {
                if (!Array.isArray(obj[feature])) {
                    obj[feature] = [];
                }
                obj[feature].push(item);
            }
        }
    }

    private assignWithoutOverride(target: any, source: any): any {
        for (const [name, existingValue] of Object.entries(source)) {
            const newValue = target[name];
            if (newValue === undefined) {
                target[name] = existingValue;
            } else if (Array.isArray(newValue) && Array.isArray(existingValue)) {
                existingValue.push(...newValue);
                target[name] = existingValue;
            }
        }
        return target;
    }

    get definitionErrors(): IParserDefinitionError[] {
        return this.wrapper.definitionErrors;
    }
}

export interface IParserDefinitionError {
    message: string
    type: number
    ruleName?: string
}

export abstract class AbstractParserErrorMessageProvider implements IParserErrorMessageProvider {

    buildMismatchTokenMessage(options: {
        expected: TokenType
        actual: IToken
        previous: IToken
        ruleName: string
    }): string {
        return defaultParserErrorProvider.buildMismatchTokenMessage(options);
    }

    buildNotAllInputParsedMessage(options: {
        firstRedundant: IToken
        ruleName: string
    }): string {
        return defaultParserErrorProvider.buildNotAllInputParsedMessage(options);
    }

    buildNoViableAltMessage(options: {
        expectedPathsPerAlt: TokenType[][][]
        actual: IToken[]
        previous: IToken
        customUserDescription: string
        ruleName: string
    }): string {
        return defaultParserErrorProvider.buildNoViableAltMessage(options);
    }

    buildEarlyExitMessage(options: {
        expectedIterationPaths: TokenType[][]
        actual: IToken[]
        previous: IToken
        customUserDescription: string
        ruleName: string
    }): string {
        return defaultParserErrorProvider.buildEarlyExitMessage(options);
    }

}

export class LangiumParserErrorMessageProvider extends AbstractParserErrorMessageProvider {

    override buildMismatchTokenMessage({ expected, actual }: {
        expected: TokenType
        actual: IToken
        previous: IToken
        ruleName: string
    }): string {
        const expectedMsg = expected.LABEL
            ? '`' + expected.LABEL + '`'
            : expected.name.endsWith(':KW')
                ? `keyword '${expected.name.substring(0, expected.name.length - 3)}'`
                : `token of type '${expected.name}'`;
        return `Expecting ${expectedMsg} but found \`${actual.image}\`.`;
    }

    override buildNotAllInputParsedMessage({ firstRedundant }: {
        firstRedundant: IToken
        ruleName: string
    }): string {
        return `Expecting end of file but found \`${firstRedundant.image}\`.`;
    }
}

export interface CompletionParserResult {
    tokens: IToken[]
    elementStack: AbstractElement[]
    tokenIndex: number
}

export class LangiumCompletionParser extends AbstractLangiumParser {
    private mainRule!: RuleResult;
    private tokens: IToken[] = [];

    private elementStack: AbstractElement[] = [];
    private lastElementStack: AbstractElement[] = [];
    private nextTokenIndex = 0;
    private stackSize = 0;

    action(): void {
        // NOOP
    }

    construct(): unknown {
        // NOOP
        return undefined;
    }

    parse(input: string): CompletionParserResult {
        this.resetState();
        const tokens = this.lexer.tokenize(input);
        this.tokens = tokens.tokens;
        this.wrapper.input = [...this.tokens];
        this.mainRule.call(this.wrapper, {});
        this.unorderedGroups.clear();
        return {
            tokens: this.tokens,
            elementStack: [...this.lastElementStack],
            tokenIndex: this.nextTokenIndex
        };
    }

    rule(rule: ParserRule, impl: RuleImpl): RuleResult {
        const ruleMethod = this.wrapper.DEFINE_RULE(withRuleSuffix(rule.name), this.startImplementation(impl).bind(this));
        if (rule.entry) {
            this.mainRule = ruleMethod;
        }
        return ruleMethod;
    }

    private resetState(): void {
        this.elementStack = [];
        this.lastElementStack = [];
        this.nextTokenIndex = 0;
        this.stackSize = 0;
    }

    private startImplementation(implementation: RuleImpl): RuleImpl {
        return (args) => {
            const size = this.keepStackSize();
            try {
                implementation(args);
            } finally {
                this.resetStackSize(size);
            }
        };
    }

    private removeUnexpectedElements(): void {
        this.elementStack.splice(this.stackSize);
    }

    keepStackSize(): number {
        const size = this.elementStack.length;
        this.stackSize = size;
        return size;
    }

    resetStackSize(size: number): void {
        this.removeUnexpectedElements();
        this.stackSize = size;
    }

    consume(idx: number, tokenType: TokenType, feature: AbstractElement): void {
        this.wrapper.wrapConsume(idx, tokenType);
        if (!this.isRecording()) {
            this.lastElementStack = [...this.elementStack, feature];
            this.nextTokenIndex = this.currIdx + 1;
        }
    }

    subrule(idx: number, rule: RuleResult, feature: AbstractElement, args: Args): void {
        this.before(feature);
        this.wrapper.wrapSubrule(idx, rule, args);
        this.after(feature);
    }

    before(element: AbstractElement): void {
        if (!this.isRecording()) {
            this.elementStack.push(element);
        }
    }

    after(element: AbstractElement): void {
        if (!this.isRecording()) {
            const index = this.elementStack.lastIndexOf(element);
            if (index >= 0) {
                this.elementStack.splice(index);
            }
        }
    }

    get currIdx(): number {
        return (this.wrapper as any).currIdx;
    }
}

const defaultConfig: IParserConfig = {
    recoveryEnabled: true,
    nodeLocationTracking: 'full',
    skipValidations: true,
    errorMessageProvider: new LangiumParserErrorMessageProvider()
};

/**
 * This class wraps the embedded actions parser of chevrotain and exposes protected methods.
 * This way, we can build the `LangiumParser` as a composition.
 */
class ChevrotainWrapper extends EmbeddedActionsParser {

    // This array is set in the base implementation of Chevrotain.
    definitionErrors: IParserDefinitionError[];

    constructor(tokens: TokenVocabulary, config?: IParserConfig) {
        const useDefaultLookahead = config && 'maxLookahead' in config;
        super(tokens, {
            ...defaultConfig,
            lookaheadStrategy: useDefaultLookahead
                ? new LLkLookaheadStrategy({ maxLookahead: config.maxLookahead })
                : new LLStarLookaheadStrategy(),
            ...config,
        });
    }

    get IS_RECORDING(): boolean {
        return this.RECORDING_PHASE;
    }

    DEFINE_RULE(name: string, impl: RuleImpl): RuleResult {
        return this.RULE(name, impl);
    }

    wrapSelfAnalysis(): void {
        this.performSelfAnalysis();
    }

    wrapConsume(idx: number, tokenType: TokenType): IToken {
        return this.consume(idx, tokenType);
    }

    wrapSubrule(idx: number, rule: RuleResult, args: Args): unknown {
        return this.subrule(idx, rule, {
            ARGS: [args]
        });
    }

    wrapOr(idx: number, choices: Array<IOrAlt<any>>): void {
        this.or(idx, choices);
    }

    wrapOption(idx: number, callback: DSLMethodOpts<unknown>): void {
        this.option(idx, callback);
    }

    wrapMany(idx: number, callback: DSLMethodOpts<unknown>): void {
        this.many(idx, callback);
    }

    wrapAtLeastOne(idx: number, callback: DSLMethodOpts<unknown>): void {
        this.atLeastOne(idx, callback);
    }
}
