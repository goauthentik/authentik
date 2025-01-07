/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/

import type { IToken, TokenType } from 'chevrotain';
import type { Range } from 'vscode-languageserver-types';
import type { AbstractElement } from '../languages/generated/ast.js';
import type { AstNode, CompositeCstNode, CstNode, LeafCstNode, RootCstNode } from '../syntax-tree.js';
import { Position } from 'vscode-languageserver-types';
import { isCompositeCstNode } from '../syntax-tree.js';
import { tokenToRange } from '../utils/cst-utils.js';

export class CstNodeBuilder {

    private rootNode!: RootCstNodeImpl;
    private nodeStack: CompositeCstNodeImpl[] = [];

    private get current(): CompositeCstNodeImpl {
        return this.nodeStack[this.nodeStack.length - 1];
    }

    buildRootNode(input: string): RootCstNode {
        this.rootNode = new RootCstNodeImpl(input);
        this.rootNode.root = this.rootNode;
        this.nodeStack = [this.rootNode];
        return this.rootNode;
    }

    buildCompositeNode(feature: AbstractElement): CompositeCstNode {
        const compositeNode = new CompositeCstNodeImpl();
        compositeNode.grammarSource = feature;
        compositeNode.root = this.rootNode;
        this.current.content.push(compositeNode);
        this.nodeStack.push(compositeNode);
        return compositeNode;
    }

    buildLeafNode(token: IToken, feature: AbstractElement): LeafCstNode {
        const leafNode = new LeafCstNodeImpl(token.startOffset, token.image.length, tokenToRange(token), token.tokenType, false);
        leafNode.grammarSource = feature;
        leafNode.root = this.rootNode;
        this.current.content.push(leafNode);
        return leafNode;
    }

    removeNode(node: CstNode): void {
        const parent = node.container;
        if (parent) {
            const index = parent.content.indexOf(node);
            if (index >= 0) {
                parent.content.splice(index, 1);
            }
        }
    }

    construct(item: { $type: string | symbol | undefined, $cstNode: CstNode }): void {
        const current: CstNode = this.current;
        // The specified item could be a datatype ($type is symbol) or a fragment ($type is undefined)
        // Only if the $type is a string, we actually assign the element
        if (typeof item.$type === 'string') {
            this.current.astNode = <AstNode>item;
        }
        item.$cstNode = current;
        const node = this.nodeStack.pop();
        // Empty composite nodes are not valid
        // Simply remove the node from the tree
        if (node?.content.length === 0) {
            this.removeNode(node);
        }
    }

    addHiddenTokens(hiddenTokens: IToken[]): void {
        for (const token of hiddenTokens) {
            const hiddenNode = new LeafCstNodeImpl(token.startOffset, token.image.length, tokenToRange(token), token.tokenType, true);
            hiddenNode.root = this.rootNode;
            this.addHiddenToken(this.rootNode, hiddenNode);
        }
    }

    private addHiddenToken(node: CompositeCstNode, token: LeafCstNode): void {
        const { offset: tokenStart, end: tokenEnd } = token;

        for (let i = 0; i < node.content.length; i++) {
            const child = node.content[i];
            const { offset: childStart, end: childEnd } = child;
            if (isCompositeCstNode(child) && tokenStart > childStart && tokenEnd < childEnd) {
                this.addHiddenToken(child, token);
                return;
            } else if (tokenEnd <= childStart) {
                node.content.splice(i, 0, token);
                return;
            }
        }

        // We know that we haven't found a suited position for the token
        // So we simply add it to the end of the current node
        node.content.push(token);
    }
}

export abstract class AbstractCstNode implements CstNode {
    abstract get offset(): number;
    abstract get length(): number;
    abstract get end(): number;
    abstract get range(): Range;

    container?: CompositeCstNode;
    grammarSource: AbstractElement;
    root: RootCstNode;
    private _astNode?: AstNode;

    /** @deprecated use `container` instead. */
    get parent(): CompositeCstNode | undefined {
        return this.container;
    }

    /** @deprecated use `grammarSource` instead. */
    get feature(): AbstractElement {
        return this.grammarSource;
    }

    get hidden(): boolean {
        return false;
    }

    get astNode(): AstNode {
        const node = typeof this._astNode?.$type === 'string' ? this._astNode : this.container?.astNode;
        if (!node) {
            throw new Error('This node has no associated AST element');
        }
        return node;
    }

    set astNode(value: AstNode) {
        this._astNode = value;
    }

    /** @deprecated use `astNode` instead. */
    get element(): AstNode {
        return this.astNode;
    }

    get text(): string {
        return this.root.fullText.substring(this.offset, this.end);
    }
}

export class LeafCstNodeImpl extends AbstractCstNode implements LeafCstNode {
    get offset(): number {
        return this._offset;
    }

    get length(): number {
        return this._length;
    }

    get end(): number {
        return this._offset + this._length;
    }

    override get hidden(): boolean {
        return this._hidden;
    }

    get tokenType(): TokenType {
        return this._tokenType;
    }

    get range(): Range {
        return this._range;
    }

    private _hidden: boolean;
    private _offset: number;
    private _length: number;
    private _range: Range;
    private _tokenType: TokenType;

    constructor(offset: number, length: number, range: Range, tokenType: TokenType, hidden = false) {
        super();
        this._hidden = hidden;
        this._offset = offset;
        this._tokenType = tokenType;
        this._length = length;
        this._range = range;
    }
}

export class CompositeCstNodeImpl extends AbstractCstNode implements CompositeCstNode {
    readonly content: CstNode[] = new CstNodeContainer(this);
    private _rangeCache?: Range;

    /** @deprecated use `content` instead. */
    get children(): CstNode[] {
        return this.content;
    }

    get offset(): number {
        return this.firstNonHiddenNode?.offset ?? 0;
    }

    get length(): number {
        return this.end - this.offset;
    }

    get end(): number {
        return this.lastNonHiddenNode?.end ?? 0;
    }

    get range(): Range {
        const firstNode = this.firstNonHiddenNode;
        const lastNode = this.lastNonHiddenNode;
        if (firstNode && lastNode) {
            if (this._rangeCache === undefined) {
                const { range: firstRange } = firstNode;
                const { range: lastRange } = lastNode;
                this._rangeCache = { start: firstRange.start, end: lastRange.end.line < firstRange.start.line ? firstRange.start : lastRange.end };
            }
            return this._rangeCache;
        } else {
            return { start: Position.create(0, 0), end: Position.create(0, 0) };
        }
    }

    private get firstNonHiddenNode(): CstNode | undefined {
        for (const child of this.content) {
            if (!child.hidden) {
                return child;
            }
        }
        return this.content[0];
    }

    private get lastNonHiddenNode(): CstNode | undefined {
        for (let i = this.content.length - 1; i >= 0; i--) {
            const child = this.content[i];
            if (!child.hidden) {
                return child;
            }
        }
        return this.content[this.content.length - 1];
    }
}

class CstNodeContainer extends Array<CstNode> {
    readonly parent: CompositeCstNode;

    constructor(parent: CompositeCstNode) {
        super();
        this.parent = parent;
        Object.setPrototypeOf(this, CstNodeContainer.prototype);
    }

    override push(...items: CstNode[]): number {
        this.addParents(items);
        return super.push(...items);
    }

    override unshift(...items: CstNode[]): number {
        this.addParents(items);
        return super.unshift(...items);
    }

    override splice(start: number, count: number, ...items: CstNode[]): CstNode[] {
        this.addParents(items);
        return super.splice(start, count, ...items);
    }

    private addParents(items: CstNode[]): void {
        for (const item of items) {
            (<AbstractCstNode>item).container = this.parent;
        }
    }
}

export class RootCstNodeImpl extends CompositeCstNodeImpl implements RootCstNode {
    private _text = '';

    override get text(): string {
        return this._text.substring(this.offset, this.end);
    }

    get fullText(): string {
        return this._text;
    }

    constructor(input?: string) {
        super();
        this._text = input ?? '';
    }
}
