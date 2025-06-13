import {
    EVENT_MESSAGE,
    EVENT_WS_MESSAGE,
    WS_MSG_TYPE_MESSAGE,
} from "@goauthentik/common/constants";
import { APIError, pluckErrorDetail } from "@goauthentik/common/errors/network";
import { MessageLevel } from "@goauthentik/common/messages";
import { SentryIgnoredError } from "@goauthentik/common/sentry";
import { WSMessage } from "@goauthentik/common/ws";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/messages/Message";
import { APIMessage } from "@goauthentik/elements/messages/Message";

import { msg } from "@lit/localize";
import { CSSResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlertGroup from "@patternfly/patternfly/components/AlertGroup/alert-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { instanceOfValidationError } from "@goauthentik/api";

/**
 * Adds a message to the message container, displaying it to the user.
 *
 * @param message The message to display.
 * @param unique Whether to only display the message if the title is unique.
 *
 * @todo Consider making this a static method on singleton {@linkcode MessageContainer}
 */
export function showMessage(message: APIMessage, unique = false): void {
    const container = document.querySelector<MessageContainer>("ak-message-container");

    if (!container) {
        throw new SentryIgnoredError("failed to find message container");
    }

    if (!message.message.trim()) {
        message.message = msg("Error");
    }

    container.addMessage(message, unique);
    container.requestUpdate();
}

/**
 * Given an API error, display the error(s) to the user.
 *
 * @param error The API error to display.
 * @param unique Whether to only display the message if the title is unique.
 * @see {@link parseAPIResponseError} for more information on how to handle API errors.
 */
export function showAPIErrorMessage(error: APIError, unique = false): void {
    if (
        instanceOfValidationError(error) &&
        Array.isArray(error.nonFieldErrors) &&
        error.nonFieldErrors.length
    ) {
        for (const nonFieldError of error.nonFieldErrors) {
            showMessage(
                {
                    level: MessageLevel.error,
                    message: nonFieldError,
                },
                unique,
            );
        }

        return;
    }

    showMessage(
        {
            level: MessageLevel.error,
            message: pluckErrorDetail(error),
        },
        unique,
    );
}

@customElement("ak-message-container")
export class MessageContainer extends AKElement {
    static styles: CSSResult[] = [
        PFBase,
        PFAlertGroup,
        css`
            /* Fix spacing between messages */
            ak-message {
                display: block;
            }

            :host([alignment="bottom"]) .pf-c-alert-group.pf-m-toast {
                bottom: var(--pf-c-alert-group--m-toast--Top);
                top: unset;
            }
        `,
    ];

    @state()
    protected messages: APIMessage[] = [];

    @property()
    public alignment: "top" | "bottom" = "top";

    constructor() {
        super();

        // Note: This seems to be susceptible to race conditions.
        // Events are dispatched regardless if the message container is listening.

        window.addEventListener(EVENT_WS_MESSAGE, ((e: CustomEvent<WSMessage>) => {
            if (e.detail.message_type !== WS_MSG_TYPE_MESSAGE) return;

            this.addMessage(e.detail as unknown as APIMessage);
        }) as EventListener);

        window.addEventListener(EVENT_MESSAGE, ((e: CustomEvent<APIMessage>) => {
            this.addMessage(e.detail);
        }) as EventListener);
    }

    public addMessage(message: APIMessage, unique = false): void {
        if (unique) {
            const match = this.messages.some((m) => m.message === message.message);

            if (match) return;
        }

        this.messages = [...this.messages, message];
    }

    #removeMessage = (message: APIMessage) => {
        this.messages = this.messages.filter((v) => v !== message);
    };

    render() {
        return html`<ul
            role="region"
            aria-label="${msg("Status messages")}"
            class="pf-c-alert-group pf-m-toast"
        >
            ${this.messages.toReversed().map((message, idx) => {
                const { message: title, description, level } = message;

                return html`<ak-message
                    ?live=${idx === 0}
                    level=${level}
                    description=${ifDefined(description)}
                    .onDismiss=${() => this.#removeMessage(message)}
                >
                    ${title}
                </ak-message>`;
            })}
        </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-message-container": MessageContainer;
    }
}
