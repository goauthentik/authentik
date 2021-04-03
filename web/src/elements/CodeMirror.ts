import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";

import CodeMirror from "codemirror";
import "codemirror/addon/display/autorefresh";
import "codemirror/mode/xml/xml.js";
import "codemirror/mode/yaml/yaml.js";
import "codemirror/mode/javascript/javascript.js";
import "codemirror/mode/python/python.js";
import CodeMirrorStyle from "codemirror/lib/codemirror.css";
import CodeMirrorTheme from "codemirror/theme/monokai.css";
import { ifDefined } from "lit-html/directives/if-defined";
import YAML from "yaml";

@customElement("ak-codemirror")
export class CodeMirrorTextarea extends LitElement {
    @property({type: Boolean})
    readOnly = false;

    @property()
    mode = "yaml";

    @property()
    name?: string;

    editor?: CodeMirror.EditorFromTextArea;

    _value?: string;

    @property()
    set value(v: string) {
        if (v === null) return;
        if (this.editor) {
            this.editor.setValue(v);
        } else {
            this._value = v;
        }
    }

    get value(): string {
        switch (this.mode.toLowerCase()) {
            case "yaml":
                return YAML.parse(this.getInnerValue());
            case "javascript":
                return JSON.parse(this.getInnerValue());
            default:
                return this.getInnerValue();
        }
    }

    private getInnerValue(): string {
        if (!this.editor) {
            return "";
        }
        return this.editor.getValue();
    }

    static get styles(): CSSResult[] {
        return [CodeMirrorStyle, CodeMirrorTheme, css`
            .CodeMirror-wrap pre {
                word-break: break-word !important;
            }
        `];
    }

    firstUpdated(): void {
        const textarea = this.shadowRoot?.querySelector("textarea");
        if (!textarea) {
            return;
        }
        this.editor = CodeMirror.fromTextArea(textarea, {
            mode: this.mode,
            theme: "monokai",
            lineNumbers: false,
            readOnly: this.readOnly,
            autoRefresh: true,
            lineWrapping: true,
            value: this._value
        });
        this.editor.on("blur", () => {
            this.editor?.save();
        });
    }

    render(): TemplateResult {
        return html`<textarea name=${ifDefined(this.name)}>${ifDefined(this._value)}</textarea>`;
    }
}
