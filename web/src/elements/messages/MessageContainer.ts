import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFAlertGroup from "@patternfly/patternfly/components/AlertGroup/alert-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { WSMessage } from "../../common/ws";
import { EVENT_WS_MESSAGE, WS_MSG_TYPE_MESSAGE } from "../../constants";
import "./Message";
import { APIMessage } from "./Message";

export function showMessage(message: APIMessage): void {
    const container = document.querySelector<MessageContainer>("ak-message-container");
    if (!container) {
        throw new Error("failed to find message container");
    }
    container.addMessage(message);
    container.requestUpdate();
}

@customElement("ak-message-container")
export class MessageContainer extends LitElement {
    @property({ attribute: false })
    messages: APIMessage[] = [];

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFAlertGroup,
            css`
                /* Fix spacing between messages */
                ak-message {
                    display: block;
                }
            `,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_WS_MESSAGE, ((e: CustomEvent<WSMessage>) => {
            if (e.detail.message_type !== WS_MSG_TYPE_MESSAGE) return;
            this.addMessage(e.detail as unknown as APIMessage);
        }) as EventListener);
    }

    addMessage(message: APIMessage): void {
        this.messages.push(message);
    }

    render(): TemplateResult {
        return html`<ul class="pf-c-alert-group pf-m-toast">
            ${this.messages.map((m) => {
                return html`<ak-message
                    .message=${m}
                    .onRemove=${(m: APIMessage) => {
                        this.messages = this.messages.filter((v) => v !== m);
                        this.requestUpdate();
                    }}
                >
                </ak-message>`;
            })}
        </ul>`;
    }
}
