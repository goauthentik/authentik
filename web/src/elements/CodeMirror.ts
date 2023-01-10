import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { html as htmlLang } from "@codemirror/lang-html";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";
import { xml } from "@codemirror/lang-xml";
import {
    LanguageSupport,
    StreamLanguage,
    defaultHighlightStyle,
    syntaxHighlighting,
} from "@codemirror/language";
import * as yamlMode from "@codemirror/legacy-modes/mode/yaml";
import { Compartment, EditorState, Extension } from "@codemirror/state";
import { EditorView, drawSelection, keymap, lineNumbers } from "@codemirror/view";
import { AKElement } from "@goauthentik/elements/Base";
import YAML from "yaml";

import { customElement, property } from "lit/decorators.js";

@customElement("ak-codemirror")
export class CodeMirrorTextarea<T> extends AKElement {
    @property({ type: Boolean })
    readOnly = false;

    @property()
    mode = "yaml";

    @property()
    name?: string;

    @property({ type: Boolean })
    parseValue = true;

    editor?: EditorView;

    _value?: string;

    theme: Compartment;

    themeLight: Extension;
    themeDark: Extension;

    @property()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any,@typescript-eslint/explicit-module-boundary-types
    set value(v: T | string) {
        if (v === null || v === undefined) return;
        // Value might be an object if within an iron-form, as that calls the getter of value
        // in the beginning and the calls this setter on reset
        let textValue = v;
        if (!(typeof v === "string" || v instanceof String)) {
            switch (this.mode.toLowerCase()) {
                case "yaml":
                    textValue = YAML.stringify(v);
                    break;
                case "javascript":
                    textValue = JSON.stringify(v);
                    break;
                default:
                    textValue = v.toString();
                    break;
            }
        }
        if (this.editor) {
            this.editor.dispatch({
                changes: { from: 0, to: this.editor.state.doc.length, insert: textValue as string },
            });
        } else {
            this._value = textValue as string;
        }
    }

    get value(): T | string {
        if (!this.parseValue) {
            return this.getInnerValue();
        }
        try {
            switch (this.mode.toLowerCase()) {
                case "yaml":
                    return YAML.parse(this.getInnerValue());
                case "javascript":
                    return JSON.parse(this.getInnerValue());
                default:
                    return this.getInnerValue();
            }
        } catch (e) {
            return this.getInnerValue();
        }
    }

    constructor() {
        super();
        this.theme = new Compartment();
        this.themeLight = EditorView.theme(
            {
                "&": {
                    backgroundColor: "var(--pf-global--BackgroundColor--light-300)",
                },
            },
            { dark: false },
        );
        this.themeDark = EditorView.theme(
            {
                "&": {
                    backgroundColor: "var(--ak-dark-background-light)",
                },
            },
            { dark: true },
        );
    }

    private getInnerValue(): string {
        if (!this.editor) {
            return "";
        }
        return this.editor.state.doc.toString();
    }

    getLanguageExtension(): LanguageSupport | undefined {
        switch (this.mode.toLowerCase()) {
            case "xml":
                return xml();
            case "javascript":
                return javascript();
            case "html":
                return htmlLang();
            case "python":
                return python();
            case "yaml":
                return new LanguageSupport(StreamLanguage.define(yamlMode.yaml));
        }
        return undefined;
    }

    firstUpdated(): void {
        const matcher = window.matchMedia("(prefers-color-scheme: light)");
        const handler = (ev?: MediaQueryListEvent) => {
            let theme;
            if (ev?.matches || matcher.matches) {
                theme = this.themeLight;
            } else {
                theme = this.themeDark;
            }
            this.editor?.dispatch({
                effects: this.theme.reconfigure(theme),
            });
        };
        const extensions = [
            history(),
            keymap.of([...defaultKeymap, ...historyKeymap]),
            syntaxHighlighting(defaultHighlightStyle),
            this.getLanguageExtension(),
            lineNumbers(),
            drawSelection(),
            EditorView.lineWrapping,
            EditorState.readOnly.of(this.readOnly),
            EditorState.tabSize.of(2),
            this.theme.of(this.themeLight),
        ];
        this.editor = new EditorView({
            extensions: extensions.filter((p) => p) as Extension[],
            root: this.shadowRoot || document,
            doc: this._value,
        });
        this.shadowRoot?.appendChild(this.editor.dom);
        matcher.addEventListener("change", handler);
        handler();
    }
}
