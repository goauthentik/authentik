/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import { defaultParserErrorProvider, EmbeddedActionsParser, LLkLookaheadStrategy } from 'chevrotain';
import { LLStarLookaheadStrategy } from 'chevrotain-allstar';
import { isAssignment, isCrossReference, isKeyword } from '../languages/generated/ast.js';
import { getTypeName, isDataTypeRule } from '../utils/grammar-utils.js';
import { assignMandatoryProperties, getContainerOfType, linkContentToContainer } from '../utils/ast-utils.js';
import { CstNodeBuilder } from './cst-node-builder.js';
export const DatatypeSymbol = Symbol('Datatype');
function isDataTypeNode(node) {
    return node.$type === DatatypeSymbol;
}
const ruleSuffix = '\u200B';
const withRuleSuffix = (name) => name.endsWith(ruleSuffix) ? name : name + ruleSuffix;
export class AbstractLangiumParser {
    constructor(services) {
        this._unorderedGroups = new Map();
        this.lexer = services.parser.Lexer;
        const tokens = this.lexer.definition;
        this.wrapper = new ChevrotainWrapper(tokens, Object.assign(Object.assign({}, services.parser.ParserConfig), { errorMessageProvider: services.parser.ParserErrorMessageProvider }));
    }
    alternatives(idx, choices) {
        this.wrapper.wrapOr(idx, choices);
    }
    optional(idx, callback) {
        this.wrapper.wrapOption(idx, callback);
    }
    many(idx, callback) {
        this.wrapper.wrapMany(idx, callback);
    }
    atLeastOne(idx, callback) {
        this.wrapper.wrapAtLeastOne(idx, callback);
    }
    isRecording() {
        return this.wrapper.IS_RECORDING;
    }
    get unorderedGroups() {
        return this._unorderedGroups;
    }
    getRuleStack() {
        return this.wrapper.RULE_STACK;
    }
    finalize() {
        this.wrapper.wrapSelfAnalysis();
    }
}
export class LangiumParser extends AbstractLangiumParser {
    get current() {
        return this.stack[this.stack.length - 1];
    }
    constructor(services) {
        super(services);
        this.nodeBuilder = new CstNodeBuilder();
        this.stack = [];
        this.assignmentMap = new Map();
        this.linker = services.references.Linker;
        this.converter = services.parser.ValueConverter;
        this.astReflection = services.shared.AstReflection;
    }
    rule(rule, impl) {
        const type = rule.fragment ? undefined : isDataTypeRule(rule) ? DatatypeSymbol : getTypeName(rule);
        const ruleMethod = this.wrapper.DEFINE_RULE(withRuleSuffix(rule.name), this.startImplementation(type, impl).bind(this));
        if (rule.entry) {
            this.mainRule = ruleMethod;
        }
        return ruleMethod;
    }
    parse(input) {
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
    startImplementation($type, implementation) {
        return (args) => {
            if (!this.isRecording()) {
                const node = { $type };
                this.stack.push(node);
                if ($type === DatatypeSymbol) {
                    node.value = '';
                }
            }
            let result;
            try {
                result = implementation(args);
            }
            catch (err) {
                result = undefined;
            }
            if (!this.isRecording() && result === undefined) {
                result = this.construct();
            }
            return result;
        };
    }
    consume(idx, tokenType, feature) {
        const token = this.wrapper.wrapConsume(idx, tokenType);
        if (!this.isRecording() && this.isValidToken(token)) {
            const leafNode = this.nodeBuilder.buildLeafNode(token, feature);
            const { assignment, isCrossRef } = this.getAssignment(feature);
            const current = this.current;
            if (assignment) {
                const convertedValue = isKeyword(feature) ? token.image : this.converter.convert(token.image, leafNode);
                this.assign(assignment.operator, assignment.feature, convertedValue, leafNode, isCrossRef);
            }
            else if (isDataTypeNode(current)) {
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
    isValidToken(token) {
        return !token.isInsertedInRecovery && !isNaN(token.startOffset) && typeof token.endOffset === 'number' && !isNaN(token.endOffset);
    }
    subrule(idx, rule, feature, args) {
        let cstNode;
        if (!this.isRecording()) {
            cstNode = this.nodeBuilder.buildCompositeNode(feature);
        }
        const subruleResult = this.wrapper.wrapSubrule(idx, rule, args);
        if (!this.isRecording() && cstNode && cstNode.length > 0) {
            this.performSubruleAssignment(subruleResult, feature, cstNode);
        }
    }
    performSubruleAssignment(result, feature, cstNode) {
        const { assignment, isCrossRef } = this.getAssignment(feature);
        if (assignment) {
            this.assign(assignment.operator, assignment.feature, result, cstNode, isCrossRef);
        }
        else if (!assignment) {
            // If we call a subrule without an assignment we either:
            // 1. append the result of the subrule (data type rule)
            // 2. override the current object with the newly parsed object
            // If the current element is an AST node and the result of the subrule
            // is a data type rule, we can safely discard the results.
            const current = this.current;
            if (isDataTypeNode(current)) {
                current.value += result.toString();
            }
            else if (typeof result === 'object' && result) {
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
    action($type, action) {
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
    construct(pop = true) {
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
        }
        else {
            assignMandatoryProperties(this.astReflection, obj);
        }
        return obj;
    }
    getAssignment(feature) {
        if (!this.assignmentMap.has(feature)) {
            const assignment = getContainerOfType(feature, isAssignment);
            this.assignmentMap.set(feature, {
                assignment: assignment,
                isCrossRef: assignment ? isCrossReference(assignment.terminal) : false
            });
        }
        return this.assignmentMap.get(feature);
    }
    assign(operator, feature, value, cstNode, isCrossRef) {
        const obj = this.current;
        let item;
        if (isCrossRef && typeof value === 'string') {
            item = this.linker.buildReference(obj, feature, cstNode, value);
        }
        else {
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
    assignWithoutOverride(target, source) {
        for (const [name, existingValue] of Object.entries(source)) {
            const newValue = target[name];
            if (newValue === undefined) {
                target[name] = existingValue;
            }
            else if (Array.isArray(newValue) && Array.isArray(existingValue)) {
                existingValue.push(...newValue);
                target[name] = existingValue;
            }
        }
        return target;
    }
    get definitionErrors() {
        return this.wrapper.definitionErrors;
    }
}
export class AbstractParserErrorMessageProvider {
    buildMismatchTokenMessage(options) {
        return defaultParserErrorProvider.buildMismatchTokenMessage(options);
    }
    buildNotAllInputParsedMessage(options) {
        return defaultParserErrorProvider.buildNotAllInputParsedMessage(options);
    }
    buildNoViableAltMessage(options) {
        return defaultParserErrorProvider.buildNoViableAltMessage(options);
    }
    buildEarlyExitMessage(options) {
        return defaultParserErrorProvider.buildEarlyExitMessage(options);
    }
}
export class LangiumParserErrorMessageProvider extends AbstractParserErrorMessageProvider {
    buildMismatchTokenMessage({ expected, actual }) {
        const expectedMsg = expected.LABEL
            ? '`' + expected.LABEL + '`'
            : expected.name.endsWith(':KW')
                ? `keyword '${expected.name.substring(0, expected.name.length - 3)}'`
                : `token of type '${expected.name}'`;
        return `Expecting ${expectedMsg} but found \`${actual.image}\`.`;
    }
    buildNotAllInputParsedMessage({ firstRedundant }) {
        return `Expecting end of file but found \`${firstRedundant.image}\`.`;
    }
}
export class LangiumCompletionParser extends AbstractLangiumParser {
    constructor() {
        super(...arguments);
        this.tokens = [];
        this.elementStack = [];
        this.lastElementStack = [];
        this.nextTokenIndex = 0;
        this.stackSize = 0;
    }
    action() {
        // NOOP
    }
    construct() {
        // NOOP
        return undefined;
    }
    parse(input) {
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
    rule(rule, impl) {
        const ruleMethod = this.wrapper.DEFINE_RULE(withRuleSuffix(rule.name), this.startImplementation(impl).bind(this));
        if (rule.entry) {
            this.mainRule = ruleMethod;
        }
        return ruleMethod;
    }
    resetState() {
        this.elementStack = [];
        this.lastElementStack = [];
        this.nextTokenIndex = 0;
        this.stackSize = 0;
    }
    startImplementation(implementation) {
        return (args) => {
            const size = this.keepStackSize();
            try {
                implementation(args);
            }
            finally {
                this.resetStackSize(size);
            }
        };
    }
    removeUnexpectedElements() {
        this.elementStack.splice(this.stackSize);
    }
    keepStackSize() {
        const size = this.elementStack.length;
        this.stackSize = size;
        return size;
    }
    resetStackSize(size) {
        this.removeUnexpectedElements();
        this.stackSize = size;
    }
    consume(idx, tokenType, feature) {
        this.wrapper.wrapConsume(idx, tokenType);
        if (!this.isRecording()) {
            this.lastElementStack = [...this.elementStack, feature];
            this.nextTokenIndex = this.currIdx + 1;
        }
    }
    subrule(idx, rule, feature, args) {
        this.before(feature);
        this.wrapper.wrapSubrule(idx, rule, args);
        this.after(feature);
    }
    before(element) {
        if (!this.isRecording()) {
            this.elementStack.push(element);
        }
    }
    after(element) {
        if (!this.isRecording()) {
            const index = this.elementStack.lastIndexOf(element);
            if (index >= 0) {
                this.elementStack.splice(index);
            }
        }
    }
    get currIdx() {
        return this.wrapper.currIdx;
    }
}
const defaultConfig = {
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
    constructor(tokens, config) {
        const useDefaultLookahead = config && 'maxLookahead' in config;
        super(tokens, Object.assign(Object.assign(Object.assign({}, defaultConfig), { lookaheadStrategy: useDefaultLookahead
                ? new LLkLookaheadStrategy({ maxLookahead: config.maxLookahead })
                : new LLStarLookaheadStrategy() }), config));
    }
    get IS_RECORDING() {
        return this.RECORDING_PHASE;
    }
    DEFINE_RULE(name, impl) {
        return this.RULE(name, impl);
    }
    wrapSelfAnalysis() {
        this.performSelfAnalysis();
    }
    wrapConsume(idx, tokenType) {
        return this.consume(idx, tokenType);
    }
    wrapSubrule(idx, rule, args) {
        return this.subrule(idx, rule, {
            ARGS: [args]
        });
    }
    wrapOr(idx, choices) {
        this.or(idx, choices);
    }
    wrapOption(idx, callback) {
        this.option(idx, callback);
    }
    wrapMany(idx, callback) {
        this.many(idx, callback);
    }
    wrapAtLeastOne(idx, callback) {
        this.atLeastOne(idx, callback);
    }
}
//# sourceMappingURL=langium-parser.js.map