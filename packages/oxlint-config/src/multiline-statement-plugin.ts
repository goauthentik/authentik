/**
 * @file The `goauthentik/multiline-statement-padding` rule: a statement that spans lines gets a
 *   blank line on each side, so a reader can see where it starts and stops without matching
 *   brackets. One rule covers what look like two habits — a big object literal jammed against the
 *   next declaration, and a multi-line call jammed against the counter after it. Both are the same
 *   thing: a statement tall enough to read as a block, sitting flush against its neighbor. Neither
 *   edge is required at a block boundary, where the brace already separates. `console.*` calls are
 *   left to `console-padding`, which groups consecutive ones — this rule would split a run that
 *   happens to contain a tall call, and a run of output is one thing.
 */

import { createPaddingHelpers } from "./padding-utils.js";
import type { AstNode, Rule } from "./plugin-types.js";

/** The object whose calls belong to `console-padding` rather than to this rule. */
const CONSOLE_OBJECT = "console";

/**
 * Statement types that can stand in a statement list and span lines.
 *
 * @remarks
 *   Block-like statements are already padded from the front by `padding-lines`; this adds their
 *   trailing edge. An exported declaration arrives wrapped, and the wrapper spans the same lines as
 *   what it wraps, so matching the wrapper is enough — without those two entries every `export` is
 *   invisible here.
 */
const MULTILINE_STATEMENT_TYPES = [
    "VariableDeclaration",
    "ExpressionStatement",
    "IfStatement",
    "ForStatement",
    "ForInStatement",
    "ForOfStatement",
    "WhileStatement",
    "DoWhileStatement",
    "SwitchStatement",
    "TryStatement",
    "FunctionDeclaration",
    "ClassDeclaration",
    "ReturnStatement",
    "TSInterfaceDeclaration",
    "TSTypeAliasDeclaration",
    "TSEnumDeclaration",
    "TSModuleDeclaration",
    "ExportNamedDeclaration",
    "ExportDefaultDeclaration",
] as const;

/**
 * Does this statement's own source span more than one line?
 *
 * @param node The statement to measure.
 * @param text The full source text of the file.
 *
 * @returns `true` when the statement contains a newline.
 */
function isMultiline(node: AstNode, text: string): boolean {
    return text.slice(node.range[0], node.range[1]).includes("\n");
}

/**
 * Is this statement a bare `console.<method>(…)` call, which `console-padding` owns?
 *
 * @param node The statement to test.
 *
 * @returns `true` for an expression statement wrapping a call on `console`.
 */
function isConsoleStatement(node: AstNode | undefined): boolean {
    if (node?.type !== "ExpressionStatement") return false;

    const callee = node.expression?.type === "CallExpression" ? node.expression.callee : undefined;

    return callee?.type === "MemberExpression" && callee.object?.name === CONSOLE_OBJECT;
}

export const multilineStatementPaddingRule: Rule = {
    meta: {
        name: "multiline-statement-padding",
        type: "layout",
        fixable: "whitespace",
        schema: [{ type: "object", additionalProperties: true }],
    },
    create(context) {
        const sourceCode = context.sourceCode ?? context.getSourceCode!();
        const text = sourceCode.getText();
        const { requirePadding } = createPaddingHelpers(context);

        function check(node: AstNode): void {
            const parent = node.parent;

            if (!parent || !Array.isArray(parent.body)) return;

            if (!isMultiline(node, text) || isConsoleStatement(node)) return;

            const body = parent.body;
            const index = body.indexOf(node);

            if (index === -1) return;

            const previous = body[index - 1];
            const next = body[index + 1];

            if (previous && !isConsoleStatement(previous)) {
                requirePadding(
                    previous,
                    node,
                    node,
                    "Expected a blank line before this multi-line statement.",
                );
            }

            if (next && !isConsoleStatement(next)) {
                requirePadding(
                    node,
                    next,
                    node,
                    "Expected a blank line after this multi-line statement.",
                );
            }
        }

        return Object.fromEntries(MULTILINE_STATEMENT_TYPES.map((type) => [type, check]));
    },
};

export default multilineStatementPaddingRule;
