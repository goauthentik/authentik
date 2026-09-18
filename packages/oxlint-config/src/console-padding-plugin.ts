/**
 * @file The `goauthentik/console-padding` rule: a `console.*` call gets a blank line on each side,
 *   so the lines that produce output stand apart from the lines that compute it. A RUN of console
 *   calls is one group — no blank lines inside it, one before the first and one after the last,
 *   because consecutive calls are one block of output. Neither edge is required where a block
 *   boundary already provides the separation: nothing before a call that opens a block, and nothing
 *   after one that closes it.
 */

import { createPaddingHelpers } from "./padding-utils.js";
import type { AstNode, Rule } from "./plugin-types.js";

/** The object whose method calls this rule treats as output. */
const CONSOLE_OBJECT = "console";

/**
 * Is this statement a bare `console.<method>(…)` call?
 *
 * @param node The statement to test.
 *
 * @returns `true` for an expression statement wrapping a call on `console`.
 */
function isConsoleStatement(node: AstNode | undefined): boolean {
    if (node?.type !== "ExpressionStatement") return false;

    const call = node.expression;

    if (call?.type !== "CallExpression") return false;

    const callee = call.callee;

    return (
        callee?.type === "MemberExpression" &&
        callee.object?.type === "Identifier" &&
        callee.object.name === CONSOLE_OBJECT
    );
}

export const consolePaddingRule: Rule = {
    meta: {
        name: "console-padding",
        type: "layout",
        fixable: "whitespace",
        schema: [{ type: "object", additionalProperties: true }],
    },
    create(context) {
        const { requirePadding } = createPaddingHelpers(context);

        return {
            ExpressionStatement(node: AstNode) {
                if (!isConsoleStatement(node)) return;

                const parent = node.parent;

                // Only statements in a statement list have neighbors to pad against.
                if (!parent || !Array.isArray(parent.body)) return;

                const body = parent.body;
                const index = body.indexOf(node);

                if (index === -1) return;

                const previous = body[index - 1];
                const next = body[index + 1];

                // Nothing before a call that opens the block, and nothing between calls in one run.
                if (previous && !isConsoleStatement(previous)) {
                    requirePadding(
                        previous,
                        node,
                        node,
                        "Expected a blank line before this console call.",
                    );
                }

                // Nothing after a call that closes the block — the brace already separates it.
                if (next && !isConsoleStatement(next)) {
                    requirePadding(
                        node,
                        next,
                        node,
                        "Expected a blank line after this console call.",
                    );
                }
            },
        };
    },
};

export default consolePaddingRule;
