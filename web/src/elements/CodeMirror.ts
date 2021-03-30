import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFForm from "@patternfly/patternfly/components/Form/form.css";

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

    private _value?: string;

    @property()
    set value(v: string) {
        this._value = v.toString();
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
        if (!this.shadowRoot) {
            return "";
        }
        const ta = this.shadowRoot?.querySelector("textarea");
        if (!ta) {
            return "";
        }
        return ta.value;
    }

    static get styles(): CSSResult[] {
        return [PFForm, CodeMirrorStyle, CodeMirrorTheme];
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
        });
        this.editor.on("blur", () => {
            this.editor?.save();
        });
    }

    render(): TemplateResult {
        return html`<textarea class="pf-c-form-control" name=${ifDefined(this.name)}>${this._value || ""}</textarea>`;
    }
}
