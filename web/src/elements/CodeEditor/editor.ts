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
import "monaco-editor/features/clipboard/register";
import "monaco-editor/features/comment/register";
import "monaco-editor/features/cursorUndo/register";
import "monaco-editor/features/find/register";
import "monaco-editor/features/folding/register";
import "monaco-editor/features/indentation/register";
import "monaco-editor/features/linesOperations/register";
import "monaco-editor/features/multicursor/register";
import "monaco-editor/features/readOnlyMessage/register";
import "monaco-editor/features/toggleTabFocusMode/register";
import "monaco-editor/features/wordOperations/register";
import "monaco-editor/languages/definitions/css/register";
import "monaco-editor/languages/definitions/html/register";
import "monaco-editor/languages/definitions/javascript/register";
import "monaco-editor/languages/definitions/python/register";
import "monaco-editor/languages/definitions/xml/register";
import "monaco-editor/languages/definitions/yaml/register";
// Monaco's package exports do not cover its CSS, so the bundlers alias this path to the file.
import MonacoStyles from "monaco-editor/min/vs/editor/editor.main.css";

import { createStyleSheetUnsafe, setAdoptedStyleSheets } from "#common/stylesheets";
import { ResolvedUITheme, ThemeChangeEvent } from "#common/theme";

import { CodeEditorMode } from "#elements/CodeEditor/shared";

import { UiThemeEnum } from "@goauthentik/api";

import { editor as monaco } from "monaco-editor/editor/editor.api";

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

function themeName(theme: ResolvedUITheme): string {
    return theme === UiThemeEnum.Dark ? "vs-dark" : "ak-light";
}

export interface MonacoEditorInit {
    mode?: CodeEditorMode;
    theme?: ResolvedUITheme;
    readOnly?: boolean;
    value?: string;
    root: ShadowRoot;
    onChange?: (value: string) => void;
}

export class MonacoEditor implements Disposable {
    public editor: monaco.IStandaloneCodeEditor;

    #container = document.createElement("div");
    #themeAbortController = new AbortController();

    constructor({
        mode = CodeEditorMode.JavaScript,
        theme = "light",
        readOnly = false,
        value = "",
        onChange = () => {},
        root,
    }: MonacoEditorInit) {
        setAdoptedStyleSheets(root, (currentStyleSheets) => [...currentStyleSheets, $MonacoStyles]);

        this.#container.className = "ak-c-code-editor";
        root.appendChild(this.#container);

        this.editor = monaco.create(this.#container, {
            value,
            language: mode,
            theme: themeName(theme),
            readOnly,
            automaticLayout: true,
            minimap: { enabled: false },
            wordWrap: "on",
            tabSize: 2,
            // The editor grows with its content, see the content size listener below.
            scrollBeyondLastLine: false,
            // Let the page scroll once the editor has nothing left to scroll.
            scrollbar: { alwaysConsumeMouseWheel: false },
            renderLineHighlightOnlyWhenFocus: true,
            padding: { top: 6, bottom: 6 },
        });

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

    public [Symbol.dispose](): void {
        this.#themeAbortController.abort();
        this.editor.dispose();
        this.#container.remove();
    }

    public dispose(): void {
        this[Symbol.dispose]();
    }
}
