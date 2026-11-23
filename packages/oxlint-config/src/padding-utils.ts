/**
 * @file The blank-line machinery the padding rules share: how to tell whether two statements are
 *   already separated, and how to ask for the separation when they are not. Every rule anchors its
 *   fix to the END of the earlier statement. That is deliberate: when two rules want the same blank
 *   line — a console call before a `return`, say — they emit the identical edit, so one is applied
 *   and the other is a no-op, instead of each inserting a newline and leaving a gap of two.
 */

import type { AstNode, Fixer, RuleContext, SourceCode } from "./plugin-types.js";

/** What a padding rule needs from its context, resolved once per `create`. */
export interface PaddingHelpers {
    /** Is there already a blank line between these two statements? */
    isPadded(from: AstNode, to: AstNode): boolean;
    /** Report and fix a missing blank line between `from` and `to`, unless one is impossible. */
    requirePadding(from: AstNode, to: AstNode, node: AstNode, message: string): void;
}

/**
 * Builds the helpers for one rule invocation.
 *
 * @remarks
 *   A gap is measured to the earliest comment leading the later statement, so the blank line lands
 *   above a statement's own comments rather than between them and their subject.
 * @param context The rule context oxlint passes to `create`.
 *
 * @returns The padding predicate and reporter, bound to this file's source text.
 */
export function createPaddingHelpers(context: RuleContext): PaddingHelpers {
    const sourceCode: SourceCode = context.sourceCode ?? context.getSourceCode!();
    const text = sourceCode.getText();
    const comments = sourceCode.getAllComments();

    function isPadded(from: AstNode, to: AstNode): boolean {
        // Two statements with no newline between them cannot be separated by a blank line. This is
        // the `;(expr)` ASI guard: the semicolon terminates the PREVIOUS statement, so the gap here
        // is zero characters wide. Asking for padding there is asking for the impossible.
        if (!text.slice(from.range[1], to.range[0]).includes("\n")) return true;

        let start = to.range[0];

        for (const comment of comments) {
            if (comment.range[0] >= from.range[1] && comment.range[1] <= to.range[0]) {
                start = Math.min(start, comment.range[0]);
            }
        }

        return (text.slice(from.range[1], start).match(/\n/g) ?? []).length >= 2;
    }

    function requirePadding(from: AstNode, to: AstNode, node: AstNode, message: string): void {
        if (isPadded(from, to)) return;

        context.report({
            node,
            message,
            fix(fixer: Fixer) {
                return fixer.insertTextAfterRange([from.range[1], from.range[1]], "\n");
            },
        });
    }

    return { isPadded, requirePadding };
}
