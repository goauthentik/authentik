import "#admin/applications/ApplicationCheckAccessForm";

import { Form } from "#elements/forms/Form";
import { ModelForm } from "#elements/forms/ModelForm";
import { ElementTagNamesOf, LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import { LitElement, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

export type CustomFormElementTagName = ElementTagNamesOf<ModelForm>;
export type CustomFormElement = HTMLElementTagNameMap[CustomFormElementTagName];
export type CustomFormProperties = LitPropertyRecord<CustomFormElement>;

@customElement("ak-proxy-form")
export class ProxyForm<T = unknown> extends Form<T> {
    static shadowRootOptions = {
        ...Form.shadowRootOptions,
        delegatesFocus: true,
    };

    protected override createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    //#region Properties

    @property({ attribute: false })
    public args: CustomFormProperties = {};

    protected innerElement: CustomFormElement | null = null;

    @property({ type: String })
    public set type(tagName: CustomFormElementTagName | null) {
        if (!tagName) {
            this.innerElement = null;
            return;
        }

        this.innerElement = document.createElement(tagName);
    }

    public get type(): CustomFormElementTagName | null {
        return this.innerElement
            ? (this.innerElement.tagName.toLowerCase() as CustomFormElementTagName)
            : null;
    }

    //#endregion

    //#region Public methods

    public override get form(): HTMLFormElement | null {
        return this.innerElement?.form || null;
    }

    public override async submit(event: SubmitEvent): Promise<unknown | undefined> {
        return this.innerElement?.submit(event);
    }

    public override reset(): void {
        this.innerElement?.reset();
    }

    public override getSuccessMessage(): string {
        return this.innerElement?.getSuccessMessage() || "";
    }

    //#endregion

    //#region Lifecycle

    public override async requestUpdate(name?: PropertyKey, oldValue?: unknown): Promise<unknown> {
        const result = super.requestUpdate(name, oldValue);

        this.innerElement?.requestUpdate();

        return result;
    }

    //#endregion

    //#region Render

    public override renderVisible(): SlottedTemplateResult {
        return guard([this.innerElement, this.args, this.viewportCheck], () => {
            if (!this.innerElement) {
                return nothing;
            }

            const tagName = this.innerElement.tagName.toLowerCase();
            const ElementConstructor = window.customElements.get(tagName) as
                | typeof LitElement
                | undefined;

            if (!ElementConstructor) {
                throw new TypeError(`Custom element ${tagName} is not defined`);
            }

            this.innerElement.viewportCheck = this.viewportCheck;

            const attributeNames = new Set(ElementConstructor.observedAttributes || []);

            for (const [key, value] of Object.entries(this.args)) {
                if (attributeNames.has(key)) {
                    this.innerElement.setAttribute(key, String(value));
                    continue;
                }

                (this.innerElement as unknown as Record<string, unknown>)[key] = value;
            }

            return this.innerElement;
        });
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-proxy-form": ProxyForm;
    }
}
