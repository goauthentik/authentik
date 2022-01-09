import CodeMirror from "codemirror";
import "codemirror/addon/dialog/dialog";
import "codemirror/addon/display/autorefresh";
import "codemirror/addon/hint/show-hint";
import "codemirror/addon/search/search";
import "codemirror/addon/search/searchcursor";
import "codemirror/mode/htmlmixed/htmlmixed.js";
import "codemirror/mode/javascript/javascript.js";
import "codemirror/mode/python/python.js";
import "codemirror/mode/xml/xml.js";
import "codemirror/mode/yaml/yaml.js";
import YAML from "yaml";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import CodeMirrorDialogStyle from "codemirror/addon/dialog/dialog.css";
import CodeMirrorShowHintStyle from "codemirror/addon/hint/show-hint.css";
import CodeMirrorStyle from "codemirror/lib/codemirror.css";
import CodeMirrorTheme from "codemirror/theme/monokai.css";

@customElement("ak-codemirror")
export class CodeMirrorTextarea extends LitElement {
    @property({ type: Boolean })
    readOnly = false;

    @property()
    mode = "yaml";

    @property()
    name?: string;

    editor?: CodeMirror.EditorFromTextArea;

    _value?: string;

    @property()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any,@typescript-eslint/explicit-module-boundary-types
    set value(v: any) {
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
            this.editor.setValue(textValue);
        } else {
            this._value = textValue;
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    get value(): any {
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

    private getInnerValue(): string {
        if (!this.editor) {
            return "";
        }
        return this.editor.getValue();
    }

    static get styles(): CSSResult[] {
        return [
            CodeMirrorStyle,
            CodeMirrorTheme,
            CodeMirrorDialogStyle,
            CodeMirrorShowHintStyle,
            css`
                .CodeMirror-wrap pre {
                    word-break: break-word !important;
                }
            `,
        ];
    }

    firstUpdated(): void {
        const textarea = this.shadowRoot?.querySelector("textarea");
        if (!textarea) {
            return;
        }
        this.editor = CodeMirror.fromTextArea(textarea, {
            mode: this.mode,
            theme: "monokai",
            lineNumbers: false, // Line Numbers seem to be broken on firefox?
            readOnly: this.readOnly,
            autoRefresh: true,
            lineWrapping: true,
            value: this._value,
        });
        this.editor.on("blur", () => {
            this.editor?.save();
        });
    }

    render(): TemplateResult {
        return html`<textarea name=${ifDefined(this.name)}>${ifDefined(this._value)}</textarea>`;
    }
}
