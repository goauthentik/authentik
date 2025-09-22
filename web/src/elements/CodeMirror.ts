import { EVENT_THEME_CHANGE } from "#common/constants";

import { FormAssociatedElement } from "#elements/forms/form-associated-element";

import { UiThemeEnum } from "@goauthentik/api";

import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
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
import { Compartment, EditorState, Extension } from "@codemirror/state";
import { oneDark, oneDarkHighlightStyle } from "@codemirror/theme-one-dark";
import { drawSelection, EditorView, keymap, lineNumbers, ViewUpdate } from "@codemirror/view";
import { Jsonifiable } from "type-fest";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { css, CSSResult } from "lit";
import { customElement, property } from "lit/decorators.js";

//#region Enums

export const CodeMirrorMode = {
    XML: "xml",
    JavaScript: "javascript",
    HTML: "html",
    CSS: "css",
    Python: "python",
    YAML: "yaml",
} as const satisfies Record<string, string>;

export type CodeMirrorMode = (typeof CodeMirrorMode)[keyof typeof CodeMirrorMode];

//#endregion

//#region Serialization

function stringify(value: unknown, mode: CodeMirrorMode): string {
    if (typeof value === "string" || value instanceof String) {
        return value.toString();
    }

    switch (mode.toLowerCase()) {
        case "yaml":
            return YAML.stringify(value);
        case "javascript":
            return JSON.stringify(value);
    }

    return String(value).toString();
}

function parse<T = unknown>(value: string, mode: CodeMirrorMode): T {
    switch (mode) {
        case CodeMirrorMode.YAML:
            return YAML.parse(value);
        case CodeMirrorMode.JavaScript:
            return JSON.parse(value);
    }

    return value as T;
}

//#endregion

//#region Language support

function createLanguageSupport(mode: CodeMirrorMode): LanguageSupport {
    switch (mode) {
        case CodeMirrorMode.XML:
            return xml();
        case CodeMirrorMode.JavaScript:
            return javascript();
        case CodeMirrorMode.HTML:
            return htmlLang();
        case CodeMirrorMode.Python:
            return python();
        case CodeMirrorMode.CSS:
            return cssLang();
        case CodeMirrorMode.YAML:
            return new LanguageSupport(StreamLanguage.define(yamlMode.yaml));
    }

    throw new TypeError(`Unrecognized CodeMirror mode: ${mode}`) as never;
}

//#endregion

@customElement("ak-codemirror")
export class CodeMirrorTextarea<
    T extends Jsonifiable = Jsonifiable,
> extends FormAssociatedElement<string> {
    //#region Styles

    public static styles: CSSResult[] = [
        // Better alignment with patternfly components
        css`
            .cm-editor {
                padding-top: calc(
                    var(--pf-global--spacer--form-element) - var(--pf-global--BorderWidth--sm)
                );
                padding-bottom: calc(
                    var(--pf-global--spacer--form-element) - var(--pf-global--BorderWidth--sm)
                );
                padding-right: var(--pf-c-form-control--inset--base);
                padding-left: var(--pf-c-form-control--inset--base);
            }
        `,
    ];

    //#endregion

    //#region Properties

    @property({ type: String })
    public mode: CodeMirrorMode = CodeMirrorMode.YAML;

    @property({ type: Boolean })
    public raw?: boolean;

    @property()
    public set value(nextValue: T) {
        if (!nextValue) {
            return;
        }

        this.#parsedValue = stringify(nextValue, this.mode);

        this.#syncValidity();

        // This is only relevant when a value has been set after the editor has been created.
        this.#editor?.dispatch({
            changes: {
                from: 0,
                to: this.#editor.state.doc.length,
                insert: this.#parsedValue,
            },
        });
    }

    public get value(): string {
        return this.#parse(this.#editor?.state);
    }

    public toJSON(): string {
        return this.value;
    }

    #syncValidity() {
        this.internals.setFormValue(this.#parsedValue || "");

        let message: string | undefined;
        const flags: ValidityStateFlags = {};

        if (this.required && !this.#parsedValue) {
            message = msg("This field is required.");
            flags.valueMissing = true;
        }

        this.internals.setValidity(flags, message, this.#editor?.dom);
    }

    //#endregion

    //#region Codemirror Internals

    #editor?: EditorView;

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

    //#region Value State

    #parsedValue?: string;

    #parse(editorState?: EditorState): string {
        if (!editorState) {
            return "";
        }

        const innerValue = editorState.doc.toString();

        if (this.raw) {
            return innerValue;
        }

        try {
            return parse(innerValue, this.mode);
        } catch (error: unknown) {
            console.warn("codemirror/parse-error", error);
            return innerValue;
        }
    }

    //#endregion

    //#region Lifecycle

    #initialize(root: ShadowRoot | Document) {
        this.addEventListener(EVENT_THEME_CHANGE, ((ev: CustomEvent<UiThemeEnum>) => {
            if (ev.detail === UiThemeEnum.Dark) {
                this.#editor?.dispatch({
                    effects: [
                        this.#theme.reconfigure(this.#themeDark),
                        this.#syntaxHighlighting.reconfigure(this.#syntaxHighlightingDark),
                    ],
                });
            } else {
                this.#editor?.dispatch({
                    effects: [
                        this.#theme.reconfigure(this.#themeLight),
                        this.#syntaxHighlighting.reconfigure(this.#syntaxHighlightingLight),
                    ],
                });
            }
        }) as EventListener);

        const dark = this.activeTheme === UiThemeEnum.Dark;

        const extensions: Array<Extension | null> = [
            history(),
            keymap.of([...defaultKeymap, ...historyKeymap]),
            createLanguageSupport(this.mode),
            lineNumbers(),
            drawSelection(),
            EditorView.lineWrapping,
            EditorView.updateListener.of((view: ViewUpdate) => {
                if (!view.docChanged) {
                    return;
                }

                this.#parsedValue = this.#parse(view.state);
                this.#syncValidity();

                this.dispatchEvent(
                    new CustomEvent("change", {
                        detail: view,
                    }),
                );
            }),
            EditorState.readOnly.of(!!this.readOnly),
            EditorState.tabSize.of(2),
            this.#syntaxHighlighting.of(
                dark ? this.#syntaxHighlightingDark : this.#syntaxHighlightingLight,
            ),
            this.#theme.of(dark ? this.#themeDark : this.#themeLight),
        ];

        this.#editor = new EditorView({
            extensions: extensions.filter(Boolean) as Extension[],
            root,
            doc: this.#parsedValue,
        });

        this.#editor.contentDOM.tabIndex = 0;
        root.appendChild(this.#editor.dom);
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        if (this.getAttribute("tabindex") === null) {
            this.setAttribute("tabindex", "0");
        }

        this.addEventListener("focus", this.#focusListener);

        this.#initialize(this.shadowRoot || document);
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();

        this.removeEventListener("focus", this.#focusListener);

        if (this.#editor) {
            console.debug("ak-codemirror: destroying editor");
            this.#editor.destroy();
        }
    }

    #focusListener = () => {
        this.#editor?.contentDOM?.focus();
    };

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-codemirror": CodeMirrorTextarea;
    }
}
