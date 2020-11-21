import { customElement, html, LitElement, property } from "lit-element";

// @ts-ignore
import CodeMirror from "codemirror";
import "codemirror/addon/display/autorefresh";
import "codemirror/mode/xml/xml.js";
import "codemirror/mode/yaml/yaml.js";
import "codemirror/mode/python/python.js";

@customElement("pb-codemirror")
export class CodeMirrorTextarea extends LitElement {
    @property()
    readOnly: boolean = false;

    @property()
    mode: string = "yaml";

    editor?: CodeMirror.EditorFromTextArea;

    createRenderRoot() {
        return this;
    }

    firstUpdated() {
        const textarea = this.querySelector("textarea");
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
        this.editor.on("blur", (e) => {
            this.editor?.save();
        });
    }
}
