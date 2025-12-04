/**
 * @file CodeMirror editor module.
 *
 * @remarks
 * This should be imported dynamically to avoid the bundle size impact of CodeMirror.
 *
 * ```ts
 * const { CodeMirrorEditor } = await import("#elements/codemirror/editor");
 * ```
 */

import { ResolvedUITheme, ThemeChangeEvent } from "#common/theme";

import { CodeMirrorMode } from "#elements/codemirror/shared";

import { UiThemeEnum } from "@goauthentik/api";

import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { css as cssLang } from "@codemirror/lang-css";
import { html as htmlLang } from "@codemirror/lang-html";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";
import { xml } from "@codemirror/lang-xml";
import {
    defaultHighlightStyle,
    LanguageSupport,
    StreamLanguage,
    syntaxHighlighting,
} from "@codemirror/language";
import * as yamlMode from "@codemirror/legacy-modes/mode/yaml";
import type { Extension } from "@codemirror/state";
import { Compartment, EditorState } from "@codemirror/state";
import { oneDark, oneDarkHighlightStyle } from "@codemirror/theme-one-dark";
import { drawSelection, EditorView, keymap, lineNumbers, ViewUpdate } from "@codemirror/view";

//#region Language support

export function createLanguageSupport(mode: CodeMirrorMode): LanguageSupport {
    return match(mode)
        .with(CodeMirrorMode.XML, () => xml())
        .with(CodeMirrorMode.JavaScript, () => javascript())
        .with(CodeMirrorMode.HTML, () => htmlLang())
        .with(CodeMirrorMode.Python, () => python())
        .with(CodeMirrorMode.CSS, () => cssLang())
        .with(CodeMirrorMode.YAML, () => new LanguageSupport(StreamLanguage.define(yamlMode.yaml)))
        .exhaustive();
}

export interface CodeMirrorInit {
    mode?: CodeMirrorMode;
    theme?: ResolvedUITheme;
    readOnly?: boolean;
    value?: string;
    root: Document | ShadowRoot;
    onUpdate?: (update: ViewUpdate) => void;
}

export class CodeMirrorEditor implements Disposable {
    public view: EditorView;
    #themeAbortController = new AbortController();

    #theme: Compartment = new Compartment();
    #syntaxHighlighting: Compartment = new Compartment();

    #themeLight = EditorView.theme(
        {
            "&": {
                backgroundColor: "var(--pf-global--BackgroundColor--light-300)",
            },
        },
        { dark: false },
    );
    #themeDark = oneDark;

    #syntaxHighlightingLight = syntaxHighlighting(defaultHighlightStyle);
    #syntaxHighlightingDark = syntaxHighlighting(oneDarkHighlightStyle);

    constructor({
        mode = CodeMirrorMode.JavaScript,
        theme = "light",
        readOnly = false,
        value = "",
        onUpdate = () => {},
        root,
    }: CodeMirrorInit) {
        const dark = theme === UiThemeEnum.Dark;

        const extensions: Array<Extension | null> = [
            history(),
            keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
            createLanguageSupport(mode),
            lineNumbers(),
            drawSelection(),
            EditorView.lineWrapping,
            EditorView.updateListener.of(onUpdate),
            EditorState.readOnly.of(!!readOnly),
            EditorState.tabSize.of(2),
            this.#syntaxHighlighting.of(
                dark ? this.#syntaxHighlightingDark : this.#syntaxHighlightingLight,
            ),
            this.#theme.of(dark ? this.#themeDark : this.#themeLight),
        ];

        this.view = new EditorView({
            extensions: extensions.filter(Boolean) as Extension[],
            root,
            doc: value,
        });

        document.addEventListener(ThemeChangeEvent.eventName, this.#themeChangeListener, {
            signal: this.#themeAbortController.signal,
        });
    }

    #themeChangeListener = (event: ThemeChangeEvent) => {
        if (!this.view) {
            return;
        }

        const effects =
            event.theme === UiThemeEnum.Dark
                ? [
                      this.#theme.reconfigure(this.#themeDark),
                      this.#syntaxHighlighting.reconfigure(this.#syntaxHighlightingDark),
                  ]
                : [
                      this.#theme.reconfigure(this.#themeLight),
                      this.#syntaxHighlighting.reconfigure(this.#syntaxHighlightingLight),
                  ];

        this.view.dispatch({ effects });
    };

    public [Symbol.dispose](): void {
        this.view.destroy();
    }

    public dispose(): void {
        this[Symbol.dispose]();
    }
}
