/**
 * @file Minimal ESLint-compatible plugin types shared by the bundled oxlint JS plugins.
 *
 * Kept local to avoid coupling to oxlint's alpha internal type surface, which is not subject to semver.
 */

export interface Comment {
    type: string;
    value: string;
    range: [number, number];
}

/** A loosely-typed AST node — only the fields the bundled rules read. */
export interface AstNode {
    type: string;
    range: [number, number];
    parent?: AstNode;
    body?: AstNode[];
}

export interface SourceCode {
    getText(): string;
    getAllComments(): Comment[];
}

export interface Fixer {
    insertTextBeforeRange(range: [number, number], text: string): unknown;
    insertTextAfterRange(range: [number, number], text: string): unknown;
    replaceTextRange(range: [number, number], text: string): unknown;
}

export interface RuleContext {
    options: unknown[];
    sourceCode?: SourceCode;
    getSourceCode?(): SourceCode;
    report(descriptor: { node: unknown; message: string; fix?(fixer: Fixer): unknown }): void;
}

export interface Rule {
    meta: { name: string; type: string; fixable?: "code" | "whitespace"; schema: unknown[] };
    create(context: RuleContext): Record<string, (node: AstNode) => void>;
}

export interface Plugin {
    meta: { name: string };
    rules: Record<string, Rule>;
}
