import "#admin/applications/ApplicationCheckAccessForm";

import type { OwnPropertyRecord } from "#common/types";

import type { AKElement } from "#elements/Base";
import { Form } from "#elements/forms/Form";
import { HTMLElementTagNameMapOf } from "#elements/types";

import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

type CustomFormElementTagName = keyof HTMLElementTagNameMapOf<Form>;
type CustomFormElement = HTMLElementTagNameMap[CustomFormElementTagName];

type FormAttributes = Partial<OwnPropertyRecord<CustomFormElement, AKElement>>;

@customElement("ak-proxy-form")
export abstract class ProxyForm<T = unknown> extends Form<T> {
    //#region Properties

    @property()
    public type?: CustomFormElementTagName;

    @property({ attribute: false })
    public args: FormAttributes = {};

    //#endregion

    protected innerElement?: CustomFormElement;

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

    public override async requestUpdate(name?: PropertyKey, oldValue?: unknown): Promise<unknown> {
        const result = super.requestUpdate(name, oldValue);

        this.innerElement?.requestUpdate();

        return result;
    }

    //#endregion

    //#region Render

    public override renderVisible(): TemplateResult {
        const elementName = this.type;
        if (!elementName) {
            throw new TypeError("No element name provided");
        }

        if (!this.innerElement) {
            this.innerElement = document.createElement(elementName);
        }

        this.innerElement.viewportCheck = this.viewportCheck;

        for (const [key, value] of Object.entries(this.args)) {
            this.innerElement.setAttribute(key, String(value));
        }

        Object.assign(this.innerElement, this.args);

        return html`${this.innerElement}`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-proxy-form": ProxyForm;
    }
}
