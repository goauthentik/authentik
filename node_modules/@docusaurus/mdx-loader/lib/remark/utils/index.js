"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.transformNode = transformNode;
exports.stringifyContent = stringifyContent;
exports.toValue = toValue;
exports.assetRequireAttributeValue = assetRequireAttributeValue;
const tslib_1 = require("tslib");
const escape_html_1 = tslib_1.__importDefault(require("escape-html"));
/**
 * Util to transform one node type to another node type
 * The input node is mutated in place
 * @param node the node to mutate
 * @param newNode what the original node should become become
 */
function transformNode(node, newNode) {
    Object.keys(node).forEach((key) => {
        // @ts-expect-error: unsafe but ok
        delete node[key];
    });
    Object.keys(newNode).forEach((key) => {
        // @ts-expect-error: unsafe but ok
        node[key] = newNode[key];
    });
    return node;
}
function stringifyContent(node, toString) {
    return node.children
        .map((item) => toValue(item, toString))
        .join('');
}
// TODO This is really a workaround, and not super reliable
// For now we only support serializing tagName, className and content
// Can we implement the TOC with real JSX nodes instead of html strings later?
function mdxJsxTextElementToHtml(element, toString) {
    const tag = element.name;
    const attributes = element.attributes.filter((child) => child.type === 'mdxJsxAttribute');
    const classAttribute = attributes.find((attr) => attr.name === 'className') ??
        attributes.find((attr) => attr.name === 'class');
    const classAttributeString = classAttribute
        ? `class="${(0, escape_html_1.default)(String(classAttribute.value))}"`
        : ``;
    const allAttributes = classAttributeString ? ` ${classAttributeString}` : '';
    const content = stringifyContent(element, toString);
    return `<${tag}${allAttributes}>${content}</${tag}>`;
}
function toValue(node, toString) {
    switch (node.type) {
        case 'mdxJsxTextElement': {
            return mdxJsxTextElementToHtml(node, toString);
        }
        case 'text':
            return (0, escape_html_1.default)(node.value);
        case 'heading':
            return stringifyContent(node, toString);
        case 'inlineCode':
            return `<code>${(0, escape_html_1.default)(node.value)}</code>`;
        case 'emphasis':
            return `<em>${stringifyContent(node, toString)}</em>`;
        case 'strong':
            return `<strong>${stringifyContent(node, toString)}</strong>`;
        case 'delete':
            return `<del>${stringifyContent(node, toString)}</del>`;
        case 'link':
            return stringifyContent(node, toString);
        default:
            return toString(node);
    }
}
function assetRequireAttributeValue(requireString, hash) {
    return {
        type: 'mdxJsxAttributeValueExpression',
        value: `require("${requireString}").default${hash && ` + '${hash}'`}`,
        data: {
            estree: {
                type: 'Program',
                body: [
                    {
                        type: 'ExpressionStatement',
                        expression: {
                            type: 'BinaryExpression',
                            left: {
                                type: 'MemberExpression',
                                object: {
                                    type: 'CallExpression',
                                    callee: {
                                        type: 'Identifier',
                                        name: 'require',
                                    },
                                    arguments: [
                                        {
                                            type: 'Literal',
                                            value: requireString,
                                            raw: `"${requireString}"`,
                                        },
                                    ],
                                    optional: false,
                                },
                                property: {
                                    type: 'Identifier',
                                    name: 'default',
                                },
                                computed: false,
                                optional: false,
                            },
                            operator: '+',
                            right: {
                                type: 'Literal',
                                value: hash,
                                raw: `"${hash}"`,
                            },
                        },
                    },
                ],
                sourceType: 'module',
                comments: [],
            },
        },
    };
}
//# sourceMappingURL=index.js.map