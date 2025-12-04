import { pluckErrorDetail } from "#common/errors/network";

import type { CodeMirrorEditor } from "#elements/CodeMirror/editor";
import {
    CodeMirrorMode,
    parseCodeMirrorSource,
    stringifyCodeMirrorSource,
} from "#elements/CodeMirror/shared";
import { FormAssociatedElement } from "#elements/forms/form-associated-element";

import type { EditorState } from "@codemirror/state";
import type { Jsonifiable } from "type-fest";

import { msg } from "@lit/localize";
import { css, CSSResult } from "lit";
import { customElement, property } from "lit/decorators.js";

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

        this.#parsedValue = stringifyCodeMirrorSource(nextValue, this.mode);

        this.#syncValidity();

        // This is only relevant when a value has been set after the editor has been created.
        this.#editor?.view?.dispatch({
            changes: {
                from: 0,
                to: this.#editor.view?.state.doc.length,
                insert: this.#parsedValue,
            },
        });
    }

    public get value(): string {
        return this.#parse(this.#editor?.view?.state);
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

        this.internals.setValidity(flags, message, this.#editor?.view?.dom);
    }

    //#endregion

    //#region Codemirror Internals

    #editor?: CodeMirrorEditor;

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
            return parseCodeMirrorSource(innerValue, this.mode);
        } catch (error: unknown) {
            const message = pluckErrorDetail(error);
            console.debug("codemirror/parse-error", message);

            return innerValue;
        }
    }

    //#endregion

    //#region Lifecycle

    async #initialize(root: ShadowRoot | Document) {
        console.debug("ak-codemirror: initializing editor...");
        const { CodeMirrorEditor } = await import("#elements/CodeMirror/editor");

        this.#editor = new CodeMirrorEditor({
            root,
            mode: this.mode,
            theme: this.activeTheme,
            readOnly: this.disabled,
            value: this.#parsedValue || "",
            onUpdate: (view) => {
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
            },
        });

        this.#editor.view.contentDOM.tabIndex = 0;
        root.appendChild(this.#editor.view.dom);
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        if (this.getAttribute("tabindex") === null) {
            this.setAttribute("tabindex", "0");
        }

        this.addEventListener("focus", this.#focusListener);

        this.role ||= "combobox";
        this.#initialize(this.shadowRoot || document);
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();

        this.removeEventListener("focus", this.#focusListener);

        if (this.#editor) {
            console.debug("ak-codemirror: destroying editor");
            this.#editor.dispose();
        }
    }

    #focusListener = () => {
        this.#editor?.view?.contentDOM?.focus();
    };

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-codemirror": CodeMirrorTextarea;
    }
}
