/**
 * @file A padding-lines rule, authored as an oxlint JS plugin (ESLint v9-compatible API).
 */

import type { AstNode, Rule } from "./plugin-types.js";

/**
 * Statement node types that require a preceding blank line: `return` plus all "block-like" statements (matching
 * ESLint's `block-like` selector).
 */
const PADDED_STATEMENT_TYPES = [
    "ReturnStatement",
    "BlockStatement",
    "IfStatement",
    "ForStatement",
    "ForInStatement",
    "ForOfStatement",
    "WhileStatement",
    "DoWhileStatement",
    "SwitchStatement",
    "TryStatement",
] as const;

export const paddingRule: Rule = {
    meta: {
        name: "padding-lines",
        type: "layout",
        fixable: "whitespace",
        schema: [{ type: "object", additionalProperties: true }],
    },
    create(context) {
        const sourceCode = context.sourceCode ?? context.getSourceCode!();
        const text = sourceCode.getText();
        const comments = sourceCode.getAllComments();

        function check(node: AstNode) {
            const parent = node.parent;

            // Only statements that are direct members of a statement list (a block/program body).
            // This naturally skips e.g. an `if` consequent block or switch-case bodies.
            if (!parent || !Array.isArray(parent.body)) return;

            const index = parent.body.indexOf(node);

            if (index <= 0) return; // first statement in the block — nothing to pad against.
            const previous = parent.body[index - 1]!;

            // A blank line should sit before the statement's own leading comments, so measure the gap
            // up to the earliest comment between the previous statement and this one.
            let start = node.range[0];

            for (const comment of comments) {
                if (comment.range[0] >= previous.range[1] && comment.range[1] <= node.range[0]) {
                    start = Math.min(start, comment.range[0]);
                }
            }

            const gap = text.slice(previous.range[1], start);

            if ((gap.match(/\n/g) ?? []).length >= 2) return; // already a blank line.

            context.report({
                node,
                message: "Expected a blank line before this statement.",
                fix(fixer) {
                    return fixer.insertTextAfterRange([previous.range[1], previous.range[1]], "\n");
                },
            });
        }

        return Object.fromEntries(PADDED_STATEMENT_TYPES.map((type) => [type, check]));
    },
};

export default paddingRule;
