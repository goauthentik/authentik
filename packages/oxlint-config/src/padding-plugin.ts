/**
 * @file The `goauthentik/padding-lines` rule, authored as an oxlint JS plugin (ESLint v9-compatible
 *   API). It requires a blank line before the statements that end a path or a step — `return`,
 *   `continue`, `break`, a bare `x++`/`x--` — and before block-like statements. Roughly ESLint's
 *   `padding-line-between-statements` with `{ blankLine: "always", prev: "*", next: "return" |
 *   "block-like" }`, widened to the rest of that family. Autofixes by inserting the blank line
 *   above any leading comments.
 */

import { createPaddingHelpers } from "./padding-utils.js";
import type { AstNode, Rule } from "./plugin-types.js";

/**
 * Statement node types that require a preceding blank line: the path-enders plus all "block-like"
 * statements, matching ESLint's `block-like` selector.
 */
const PADDED_STATEMENT_TYPES = [
    "ReturnStatement",
    "ContinueStatement",
    "BreakStatement",
    "BlockStatement",
    "IfStatement",
    "ForStatement",
    "ForInStatement",
    "ForOfStatement",
    "WhileStatement",
    "DoWhileStatement",
    "SwitchStatement",
    "TryStatement",
    // An interface or type alias with a body reads as a block too — same braces, same weight on the
    // page — so it wants the same separation from whatever precedes it.
    "TSInterfaceDeclaration",
    "TSTypeAliasDeclaration",
    "TSEnumDeclaration",
    "TSModuleDeclaration",
] as const;

/**
 * Does this node type require a preceding blank line?
 *
 * @param type The node type to test, if the node has one.
 *
 * @returns `true` when a statement of this type must be preceded by a blank line.
 */
function isPaddedType(type: string | undefined): boolean {
    return !!type && (PADDED_STATEMENT_TYPES as readonly string[]).includes(type);
}

export const paddingRule: Rule = {
    meta: {
        name: "padding-lines",
        type: "layout",
        fixable: "whitespace",
        schema: [{ type: "object", additionalProperties: true }],
    },
    create(context) {
        const { requirePadding } = createPaddingHelpers(context);

        function check(node: AstNode) {
            const parent = node.parent;

            // Only statements that are direct members of a statement list (a block or program body).
            // This naturally skips an `if` consequent block or a switch-case body.
            if (!parent || !Array.isArray(parent.body)) return;

            const index = parent.body.indexOf(node);

            // First statement in the block — nothing to pad against.
            if (index <= 0) return;

            requirePadding(
                parent.body[index - 1]!,
                node,
                node,
                "Expected a blank line before this statement.",
            );
        }

        return {
            ...Object.fromEntries(PADDED_STATEMENT_TYPES.map((type) => [type, check])),
            // A bare `x++` / `x--` is a counter step, and reads like one only when it stands apart.
            // It arrives as an ExpressionStatement, so it cannot be matched by node type alone.
            ExpressionStatement(node: AstNode) {
                if (node.expression?.type === "UpdateExpression") {
                    check(node);
                }
            },
            // An exported declaration arrives wrapped. Look through the wrapper so
            // `export interface Foo {}` is padded exactly like the unexported form.
            ExportNamedDeclaration(node: AstNode) {
                if (isPaddedType(node.declaration?.type)) {
                    check(node);
                }
            },
            ExportDefaultDeclaration(node: AstNode) {
                if (isPaddedType(node.declaration?.type)) {
                    check(node);
                }
            },
        };
    },
};

export default paddingRule;
