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
import { oneDark } from "@codemirror/theme-one-dark";
import { ViewUpdate } from "@codemirror/view";
import { EditorView, drawSelection, keymap, lineNumbers } from "@codemirror/view";
import { EVENT_THEME_CHANGE } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import YAML from "yaml";

import { customElement, property } from "lit/decorators.js";

import { UiThemeEnum } from "@goauthentik/api";

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
        this.themeDark = oneDark;
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
        this.addEventListener(EVENT_THEME_CHANGE, ((ev: CustomEvent<UiThemeEnum>) => {
            if (ev.detail === UiThemeEnum.Dark) {
                this.editor?.dispatch({
                    effects: this.theme.reconfigure(this.themeDark),
                });
            } else {
                this.editor?.dispatch({
                    effects: this.theme.reconfigure(this.themeLight),
                });
            }
        }) as EventListener);
        const extensions = [
            history(),
            keymap.of([...defaultKeymap, ...historyKeymap]),
            syntaxHighlighting(defaultHighlightStyle),
            this.getLanguageExtension(),
            lineNumbers(),
            drawSelection(),
            EditorView.lineWrapping,
            EditorView.updateListener.of((v: ViewUpdate) => {
                if (!v.docChanged) {
                    return;
                }
                this.dispatchEvent(
                    new CustomEvent("change", {
                        detail: v,
                    }),
                );
            }),
            EditorState.readOnly.of(this.readOnly),
            EditorState.tabSize.of(2),
            this.theme.of(this.activeTheme === UiThemeEnum.Dark ? this.themeDark : this.themeLight),
        ];
        this.editor = new EditorView({
            extensions: extensions.filter((p) => p) as Extension[],
            root: this.shadowRoot || document,
            doc: this._value,
        });
        this.shadowRoot?.appendChild(this.editor.dom);
    }
}
