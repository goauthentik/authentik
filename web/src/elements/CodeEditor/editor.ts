/**
 * @remarks
 *   This should be imported dynamically to avoid the bundle size impact of Monaco.
 *
 *   ```ts
 *   const { MonacoEditor } = await import("#elements/CodeEditor/editor");
 *   ```
 * @file Monaco editor module.
 */

import "monaco-editor/features/bracketMatching/register";
import "monaco-editor/features/caretOperations/register";
import "monaco-editor/features/clipboard/register";
import "monaco-editor/features/comment/register";
import "monaco-editor/features/contextmenu/register";
import "monaco-editor/features/cursorUndo/register";
import "monaco-editor/features/find/register";
import "monaco-editor/features/folding/register";
import "monaco-editor/features/gotoLine/register";
import "monaco-editor/features/hover/register";
import "monaco-editor/features/indentation/register";
import "monaco-editor/features/linesOperations/register";
import "monaco-editor/features/multicursor/register";
import "monaco-editor/features/readOnlyMessage/register";
import "monaco-editor/features/smartSelect/register";
import "monaco-editor/features/snippet/register";
import "monaco-editor/features/toggleTabFocusMode/register";
import "monaco-editor/features/wordHighlighter/register";
import "monaco-editor/features/wordOperations/register";
import "monaco-editor/features/wordPartOperations/register";
import "monaco-editor/languages/definitions/css/register";
import "monaco-editor/languages/definitions/html/register";
import "monaco-editor/languages/definitions/javascript/register";
import "monaco-editor/languages/definitions/python/register";
import "monaco-editor/languages/definitions/xml/register";
import "monaco-editor/languages/definitions/yaml/register";
// The suggestion widget has no feature entry point of its own.
import "monaco-editor/editor/contrib/suggest/browser/suggestController";
// Monaco's package exports do not cover its CSS, so the bundlers alias this path to the file.
import MonacoStyles from "monaco-editor/min/vs/editor/editor.main.css";

import { createStyleSheetUnsafe, setAdoptedStyleSheets } from "#common/stylesheets";
import { ResolvedUITheme, ThemeChangeEvent } from "#common/theme";

import type { Disposable as SchemaAssociation } from "#elements/CodeEditor/languages/schemas";
import type { LanguageService } from "#elements/CodeEditor/languages/types";
import { CodeEditorMode, CodeEditorSchema } from "#elements/CodeEditor/shared";
import { OneDark } from "#elements/CodeEditor/themes/one-dark";

import { UiThemeEnum } from "@goauthentik/api";

import { languages, editor as monaco, Uri } from "monaco-editor/editor/editor.api";

const $MonacoStyles = createStyleSheetUnsafe(MonacoStyles);

/**
 * The rules of Monaco's stylesheet that must apply to the document rather than the editor's
 * shadow root:
 *
 * - Chromium ignores `@font-face` rules in a shadow root's styles, so the icon font only loads when
 *   the document declares it.
 * - Monaco appends its screen reader live region, which announces e.g. search results, to the
 *   document body. Without the rule that moves it off screen, the announcements are visible below
 *   the page.
 */
const $MonacoDocumentStyles = new CSSStyleSheet();

for (const rule of $MonacoStyles.cssRules) {
    if (
        rule instanceof CSSFontFaceRule ||
        (rule instanceof CSSStyleRule && rule.selectorText === ".monaco-aria-container")
    ) {
        $MonacoDocumentStyles.insertRule(rule.cssText);
    }
}

setAdoptedStyleSheets(document, (currentStyleSheets) => [
    ...currentStyleSheets,
    $MonacoDocumentStyles,
]);

// Keeps the editor apart from the white form behind it, as PatternFly's
// `--pf-global--BackgroundColor--light-300` does for other fields.
// Monaco themes only take literal colors.
monaco.defineTheme("ak-light", {
    base: "vs",
    inherit: true,
    rules: [],
    colors: { "editor.background": "#f0f0f0" },
});

monaco.defineTheme("ak-dark", OneDark);

// JSON's language service loads with the first JSON editor, but models need its ID up front.
languages.register({
    id: "json",
    extensions: [".json"],
    aliases: ["JSON", "json"],
    mimetypes: ["application/json"],
});

/**
 * Language services, loaded with the first editor of their language.
 */
const LanguageServices: Partial<Record<CodeEditorMode, () => Promise<LanguageService>>> = {
    [CodeEditorMode.CSS]: () => import("#elements/CodeEditor/languages/css-service"),
    [CodeEditorMode.JSON]: () => import("#elements/CodeEditor/languages/json-service"),
    [CodeEditorMode.Python]: () => import("#elements/CodeEditor/languages/python-service"),
};

function loadLanguageService(mode: string): Promise<LanguageService | null> {
    const load = LanguageServices[mode as CodeEditorMode];

    if (!load) return Promise.resolve(null);

    return load().catch((error: unknown) => {
        console.warn("code-editor: failed to load language service", mode, error);

        return null;
    });
}

/**
 * Python is indented by four spaces by convention, and in authentik's documentation.
 */
function tabSize(mode: string): number {
    return mode === CodeEditorMode.Python ? 4 : 2;
}

function themeName(theme: ResolvedUITheme): string {
    return theme === UiThemeEnum.Dark ? "ak-dark" : "ak-light";
}

let modelCount = 0;

export interface MonacoEditorInit {
    mode?: CodeEditorMode;
    theme?: ResolvedUITheme;
    readOnly?: boolean;
    value?: string;
    schema?: CodeEditorSchema;
    root: ShadowRoot;
    onChange?: (value: string) => void;
}

export class MonacoEditor implements Disposable {
    public editor: monaco.IStandaloneCodeEditor;

    #container = document.createElement("div");
    #model: monaco.ITextModel;
    #themeAbortController = new AbortController();

    #schema?: CodeEditorSchema;
    #schemaAssociation?: SchemaAssociation;
    #schemaRequest = 0;
    #disposed = false;

    constructor({
        mode = CodeEditorMode.JavaScript,
        theme = "light",
        readOnly = false,
        value = "",
        schema,
        onChange = () => {},
        root,
    }: MonacoEditorInit) {
        setAdoptedStyleSheets(root, (currentStyleSheets) =>
            currentStyleSheets.includes($MonacoStyles)
                ? currentStyleSheets
                : [...currentStyleSheets, $MonacoStyles],
        );

        this.#container.className = "ak-c-code-editor";
        root.appendChild(this.#container);

        // Language services match schemas to models by URI.
        this.#model = monaco.createModel(
            value,
            mode,
            Uri.parse(`inmemory://ak-code-editor/${++modelCount}.${mode}`),
        );

        this.#model.updateOptions({ tabSize: tabSize(mode) });

        this.editor = monaco.create(this.#container, {
            model: this.#model,
            theme: themeName(theme),
            readOnly,
            automaticLayout: true,
            minimap: { enabled: false },
            wordWrap: "on",
            // The editor grows with its content, see the content size listener below.
            scrollBeyondLastLine: false,
            // Let the page scroll once the editor has nothing left to scroll.
            scrollbar: { alwaysConsumeMouseWheel: false },
            renderLineHighlightOnlyWhenFocus: true,
            renderWhitespace: "selection",
            guides: { bracketPairs: "active" },
            padding: { top: 6, bottom: 6 },
            // Word suggestions are computed in a web worker, which is not bundled.
            wordBasedSuggestions: "off",
        });

        this.#schema = schema;
        this.#loadLanguage();

        // Monaco needs an explicit height. Following the content keeps short values compact,
        // and the container's CSS `max-height` caps long ones, which then scroll.
        const followContentHeight = () => {
            this.#container.style.height = `${this.editor.getContentHeight()}px`;
        };

        followContentHeight();
        this.editor.onDidContentSizeChange(followContentHeight);

        // Monaco scrolls its own viewport to reveal a search match or the cursor, which does
        // not help while part of the editor is scrolled out of the surrounding form or modal.
        // Clicks are left alone, since scrolling the page under the pointer turns them into
        // selections.
        this.editor.onDidChangeCursorSelection(({ source }) => {
            if (source === "mouse") return;

            this.#container.scrollIntoView({ block: "nearest" });
        });

        this.editor.onDidChangeModelContent(() => {
            onChange(this.editor.getValue());
        });

        document.addEventListener(
            ThemeChangeEvent.eventName,
            (event) => monaco.setTheme(themeName(event.theme)),
            { signal: this.#themeAbortController.signal },
        );
    }

    //#region Language

    public setMode(mode: CodeEditorMode): void {
        monaco.setModelLanguage(this.#model, mode);
        this.#model.updateOptions({ tabSize: tabSize(mode) });

        this.#loadLanguage();
    }

    public setReadOnly(readOnly: boolean): void {
        this.editor.updateOptions({ readOnly });
    }

    public setSchema(schema: CodeEditorSchema | undefined): void {
        this.#schema = schema;

        this.#loadLanguage();
    }

    /**
     * Loads the model's language service, then applies the schema if the service takes one.
     */
    async #loadLanguage() {
        const request = ++this.#schemaRequest;
        const language = this.#model.getLanguageId();

        this.#schemaAssociation?.dispose();
        this.#schemaAssociation = undefined;

        const service = await loadLanguageService(language);

        if (request !== this.#schemaRequest || this.#disposed || !this.#schema) return;

        this.#schemaAssociation = service?.associateSchema?.(
            this.#model.uri.toString(),
            this.#schema,
        );
    }

    //#endregion

    public [Symbol.dispose](): void {
        this.#disposed = true;
        this.#schemaAssociation?.dispose();
        this.#themeAbortController.abort();
        this.editor.dispose();
        this.#model.dispose();
        this.#container.remove();
    }

    public dispose(): void {
        this[Symbol.dispose]();
    }
}
