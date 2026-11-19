/**
 * @remarks
 *   Expressions are the body of a function the server wraps them in, so `return` is valid at the
 *   top level and the context variables are that function's parameters, which are not known here.
 * @file Python suggestions.
 */

import { editor, languages, Range } from "monaco-editor/editor/editor.api";
import { language } from "monaco-editor/languages/definitions/python/python";

/**
 * The keywords and builtins Monaco highlights, without dunder names such as `__init__`.
 */
const Keywords = Array.from(new Set(language.keywords as string[])).filter(
    (keyword) => !keyword.startsWith("__"),
);

const KeywordSet = new Set(Keywords);

const Snippets: Record<string, string> = {
    "if": "if ${1:condition}:\n\t${0:pass}",
    "if/else": "if ${1:condition}:\n\t${2:pass}\nelse:\n\t${0:pass}",
    "for": "for ${1:item} in ${2:items}:\n\t${0:pass}",
    "try/except": "try:\n\t${1:pass}\nexcept ${2:Exception} as ${3:exc}:\n\t${0:pass}",
    "def": "def ${1:name}(${2}):\n\t${0:pass}",
    "with": "with ${1:expression} as ${2:target}:\n\t${0:pass}",
};

/**
 * Names already written in the expression, as Monaco's tokenizer finds them, so names in strings
 * and comments are left out.
 */
function collectNames(model: editor.ITextModel, currentWord: string): Set<string> {
    const names = new Set<string>();
    const lines = model.getLinesContent();

    editor.tokenize(model.getValue(), "python").forEach((tokens, lineIndex) => {
        const line = lines[lineIndex];

        tokens.forEach((token, tokenIndex) => {
            if (token.type !== "identifier.python") return;

            const end = tokens[tokenIndex + 1]?.offset ?? line.length;
            const name = line.slice(token.offset, end);

            if (name !== currentWord && !KeywordSet.has(name)) names.add(name);
        });
    });

    return names;
}

languages.registerCompletionItemProvider("python", {
    provideCompletionItems(model, position) {
        const word = model.getWordUntilPosition(position);

        const range = new Range(
            position.lineNumber,
            word.startColumn,
            position.lineNumber,
            word.endColumn,
        );

        // Attribute access needs to know the object's type.
        const before = model.getLineContent(position.lineNumber).slice(0, word.startColumn - 1);

        if (before.trimEnd().endsWith(".")) return { suggestions: [] };

        const { CompletionItemKind: Kind, CompletionItemInsertTextRule: Rule } = languages;

        const suggestions: languages.CompletionItem[] = [
            ...Keywords.map((label) => ({
                label,
                kind: Kind.Keyword,
                insertText: label,
                range,
            })),
            ...Object.entries(Snippets).map(([label, insertText]) => ({
                label,
                kind: Kind.Snippet,
                insertText,
                insertTextRules: Rule.InsertAsSnippet,
                range,
            })),
            ...Array.from(collectNames(model, word.word), (label) => ({
                label,
                kind: Kind.Variable,
                insertText: label,
                range,
            })),
        ];

        return { suggestions };
    },
});
