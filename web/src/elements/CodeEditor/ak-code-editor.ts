import { pluckErrorDetail } from "#common/errors/network";

import type { MonacoEditor } from "#elements/CodeEditor/editor";
import {
    CodeEditorMode,
    parseCodeEditorSource,
    stringifyCodeEditorSource,
} from "#elements/CodeEditor/shared";
import { FormAssociatedElement } from "#elements/forms/form-associated-element";

import type { Jsonifiable } from "type-fest";

import { msg } from "@lit/localize";
import { css, CSSResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-code-editor")
export class CodeEditor<T extends Jsonifiable = Jsonifiable> extends FormAssociatedElement<string> {
    //#region Styles

    public static styles: CSSResult[] = [
        css`
            :host {
                display: block;
            }

            .ak-c-code-editor {
                min-height: 3rem;
                max-height: 50vh;
            }
        `,
    ];

    //#endregion

    //#region Properties

    @property({ type: String })
    public mode: CodeEditorMode = CodeEditorMode.YAML;

    @property({ type: Boolean })
    public raw?: boolean;

    @property()
    public set value(nextValue: T) {
        if (!nextValue) {
            return;
        }

        this.#source = stringifyCodeEditorSource(nextValue, this.mode);

        this.#syncValidity();

        // This is only relevant when a value has been set after the editor has been created.
        this.#editor?.editor.setValue(this.#source);
    }

    public get value(): string {
        if (typeof this.#source === "undefined") {
            return "";
        }

        return this.#parseSource(this.#source);
    }

    public toJSON(): string {
        return this.value;
    }

    #syncValidity() {
        this.internals.setFormValue(this.#source || "");

        let message: string | undefined;
        const flags: ValidityStateFlags = {};

        if (this.required && !this.#source) {
            message = msg("This field is required.");
            flags.valueMissing = true;
        }

        this.internals.setValidity(flags, message, this.#editor?.editor.getDomNode() ?? undefined);
    }

    //#endregion

    //#region Monaco Internals

    #editor?: MonacoEditor;

    //#region Value State

    /**
     * The editor's text.
     *
     * @remarks
     *   The editor is created once the element is shown, from a lazily imported module,
     *   so a form submitted before then still reads the value that was set on the element.
     */
    #source?: string;

    #parseSource(innerValue: string): string {
        if (this.raw) {
            return innerValue;
        }

        try {
            return parseCodeEditorSource(innerValue, this.mode);
        } catch (error: unknown) {
            const message = pluckErrorDetail(error);

            console.debug("code-editor/parse-error", message);

            return innerValue;
        }
    }

    //#endregion

    //#region Lifecycle

    async #initialize(root: ShadowRoot) {
        console.debug("ak-code-editor: initializing editor...");

        const { MonacoEditor } = await import("#elements/CodeEditor/editor");

        // The element may have been removed while the editor module was loading.
        if (!this.isConnected || this.#editor) {
            return;
        }

        this.#editor = new MonacoEditor({
            root,
            mode: this.mode,
            theme: this.activeTheme,
            readOnly: this.readOnly || this.disabled,
            value: this.#source || "",
            onChange: (source) => {
                this.#source = source;
                this.#syncValidity();

                this.dispatchEvent(new Event("change"));
            },
        });
    }

    /**
     * Defers loading Monaco until the element is shown, since many forms keep their code
     * field in a collapsed group that is usually never opened.
     */
    #visibilityObserver = new IntersectionObserver((entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;

        this.#visibilityObserver.disconnect();
        this.#initialize(this.renderRoot as ShadowRoot);
    });

    public override connectedCallback(): void {
        super.connectedCallback();

        this.#visibilityObserver.observe(this);
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();

        this.#visibilityObserver.disconnect();

        if (this.#editor) {
            console.debug("ak-code-editor: destroying editor");

            this.#editor.dispose();
            this.#editor = undefined;
        }
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-code-editor": CodeEditor;
    }
}
