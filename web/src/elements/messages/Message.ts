import { MessageLevel } from "@goauthentik/common/messages";
import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFAlertGroup from "@patternfly/patternfly/components/AlertGroup/alert-group.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * An error message returned from an API endpoint.
 *
 * @remarks
 * This interface must align with the server-side event dispatcher.
 *
 * @see {@link ../authentik/core/templates/base/skeleton.html}
 */
export interface APIMessage {
    level: MessageLevel;
    message: string;
    description?: string;
}

const LevelIconMap = {
    [MessageLevel.error]: "fas fa-exclamation-circle",
    [MessageLevel.warning]: "fas fa-exclamation-triangle",
    [MessageLevel.success]: "fas fa-check-circle",
    [MessageLevel.info]: "fas fa-info",
} as const satisfies Record<MessageLevel, string>;

const LevelARIALiveMap = {
    [MessageLevel.error]: "assertive",
    [MessageLevel.warning]: "assertive",
    [MessageLevel.success]: "polite",
    [MessageLevel.info]: "polite",
} as const satisfies Record<MessageLevel, string>;

@customElement("ak-message")
export class Message extends AKElement {
    static styles: CSSResult[] = [PFBase, PFButton, PFAlert, PFAlertGroup];

    //#region Properties

    @property({ type: String })
    public description?: string;

    @property({ type: String })
    public level?: MessageLevel;

    @property({ attribute: false })
    public onDismiss?: (message: APIMessage) => void;

    @property({ type: Boolean })
    public live?: boolean;

    @property({ type: Number })
    public lifetime?: number = 8_000;

    //#endregion

    //#region Lifecycle

    #timeoutID = -1;

    #scheduleDismiss = () => {
        clearTimeout(this.#timeoutID);
        this.#timeoutID = -1;

        if (typeof this.lifetime !== "number" || !isFinite(this.lifetime)) {
            return;
        }

        if (!this.onDismiss) return;

        this.#timeoutID = setTimeout(this.onDismiss, this.lifetime);
    };

    public firstUpdated() {
        this.#scheduleDismiss();
    }

    public willUpdate(changed: PropertyValues<this>) {
        if (changed.has("lifetime") && this.lifetime) {
            this.#scheduleDismiss();
        }
    }

    public disconnectedCallback() {
        clearTimeout(this.#timeoutID);
    }

    //#endregion

    public render() {
        const { description, level = MessageLevel.info } = this;
        const ariaLive = this.live ? LevelARIALiveMap[level] : "off";

        return html`<li
            role="status"
            aria-live="${ariaLive}"
            aria-atomic="true"
            aria-labelledby="message-title"
            aria-describedby=${ifDefined(description ? "message-description" : undefined)}
            class="pf-c-alert-group__item"
        >
            <div
                class="${classMap({
                    "pf-c-alert": true,
                    [`pf-m-${level}`]: true,
                    "pf-m-danger": level === MessageLevel.error,
                })}"
            >
                <div class="pf-c-alert__icon">
                    <i class="${LevelIconMap[level]}"></i>
                </div>
                <p class="pf-c-alert__title" id="message-title">
                    <slot></slot>
                </p>
                ${description
                    ? html`<div class="pf-c-alert__description" id="message-description">
                          <p>${description}</p>
                      </div>`
                    : nothing}
                <div class="pf-c-alert__action">
                    <button
                        aria-label=${msg("Dismiss")}
                        class="pf-c-button pf-m-plain"
                        type="button"
                        @click=${this.onDismiss}
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
