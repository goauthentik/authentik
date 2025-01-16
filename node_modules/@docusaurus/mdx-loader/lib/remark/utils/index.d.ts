/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import type { Parent, Node } from 'unist';
import type { PhrasingContent, Heading } from 'mdast';
import type { MdxJsxAttributeValueExpression, MdxJsxTextElement } from 'mdast-util-mdx';
/**
 * Util to transform one node type to another node type
 * The input node is mutated in place
 * @param node the node to mutate
 * @param newNode what the original node should become become
 */
export declare function transformNode<NewNode extends Node>(node: Node, newNode: NewNode): NewNode;
export declare function stringifyContent(node: Parent, toString: (param: unknown) => string): string;
export declare function toValue(node: PhrasingContent | Heading | MdxJsxTextElement, toString: (param: unknown) => string): string;
export declare function assetRequireAttributeValue(requireString: string, hash: string): MdxJsxAttributeValueExpression;
//# sourceMappingURL=index.d.ts.map