/**
 * @file Minimal ESLint-compatible plugin types shared by the bundled oxlint JS plugins. Kept local
 *   to avoid coupling to oxlint's alpha internal type surface, which is not subject to semver.
 */

export interface Comment {
    type: string;
    value: string;
    range: [number, number];
}

/**
 * A loosely-typed AST node — only the fields the bundled rules read.
 *
 * @remarks
 *   The shape is loose on purpose: a field is declared when a rule reads it. Every field a rule
 *   reads belongs here rather than in a private mirror inside one plugin, so the next rule that
 *   needs it finds it already declared.
 */
export interface AstNode {
    type: string;
    range: [number, number];
    parent?: AstNode;
    /** A statement-list body (block or program) is an array; a loop body is a single statement. */
    body?: AstNode[] | AstNode;
    /** An expression statement's expression. */
    expression?: AstNode;
    /** An export statement's inner declaration. */
    declaration?: AstNode | null;
    /** A call expression's callee. */
    callee?: AstNode;
    /** A member expression's object. */
    object?: AstNode;
    /** An identifier's name. */
    name?: string;
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
