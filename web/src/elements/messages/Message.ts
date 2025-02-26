import { MessageLevel } from "@goauthentik/common/messages";
import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFAlertGroup from "@patternfly/patternfly/components/AlertGroup/alert-group.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface APIMessage {
    level: MessageLevel;
    tags?: string;
    message: string;
    description?: string;
}

const LEVEL_ICON_MAP: { [key: string]: string } = {
    error: "fas fa-exclamation-circle",
    warning: "fas fa-exclamation-triangle",
    success: "fas fa-check-circle",
    info: "fas fa-info",
};

@customElement("ak-message")
export class Message extends AKElement {
    @property({ attribute: false })
    message?: APIMessage;

    @property({ type: Number })
    removeAfter = 8000;

    @property({ attribute: false })
    onRemove?: (m: APIMessage) => void;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFAlert, PFAlertGroup];
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
            <div
                class="pf-c-alert pf-m-${this.message?.level} ${this.message?.level ===
                MessageLevel.error
                    ? "pf-m-danger"
                    : ""}"
            >
                <div class="pf-c-alert__icon">
                    <i class="${this.message ? LEVEL_ICON_MAP[this.message.level] : ""}"></i>
                </div>
                <p class="pf-c-alert__title">${this.message?.message}</p>
                ${this.message?.description &&
                html`<div class="pf-c-alert__description">
                    <p>${this.message.description}</p>
                </div>`}
                <div class="pf-c-alert__action">
                    <button
                        class="pf-c-button pf-m-plain"
                        type="button"
                        @click=${() => {
                            if (!this.message) return;
                            if (!this.onRemove) return;
                            this.onRemove(this.message);
                        }}
                    >
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                </div>
            </div>
        </li>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-message": Message;
    }
}
