import { customElement, html, LitElement, property, TemplateResult } from "lit-element";

export interface APIMessage {
    level_tag: string;
    tags?: string;
    message: string;
}

const LEVEL_ICON_MAP: { [key: string]: string } = {
    error: "fas fa-exclamation-circle",
    warning: "fas fa-exclamation-triangle",
    success: "fas fa-check-circle",
    info: "fas fa-info",
};

@customElement("ak-message")
export class Message extends LitElement {

    @property({attribute: false})
    message?: APIMessage;

    @property({type: Number})
    removeAfter = 3000;

    @property({attribute: false})
    onRemove?: (m: APIMessage) => void;

    createRenderRoot(): ShadowRoot | Element {
        return this;
    }

    firstUpdated(): void {
        setTimeout(() => {
            if (!this.message) return;
            if (!this.onRemove) return;
            this.onRemove(this.message);
        }, this.removeAfter);
    }

    render(): TemplateResult {
        return html`<li class="pf-c-alert-group__item">
            <div class="pf-c-alert pf-m-${this.message?.level_tag} ${this.message?.level_tag === "error" ? "pf-m-danger" : ""}">
                <div class="pf-c-alert__icon">
                    <i class="${this.message ? LEVEL_ICON_MAP[this.message.level_tag] : ""}"></i>
                </div>
                <p class="pf-c-alert__title">
                    ${this.message?.message}
                </p>
            </div>
        </li>`;
    }

}
