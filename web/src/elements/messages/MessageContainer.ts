import "#elements/messages/Message";

import { EVENT_MESSAGE, EVENT_WS_MESSAGE, WS_MSG_TYPE_MESSAGE } from "#common/constants";
import { APIError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";
import { SentryIgnoredError } from "#common/sentry/index";
import { WSMessage } from "#common/ws";

import { AKElement } from "#elements/Base";
import { APIMessage } from "#elements/messages/Message";

import { instanceOfValidationError } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAlertGroup from "@patternfly/patternfly/components/AlertGroup/alert-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * Adds a message to the message container, displaying it to the user.
 *
 * @param message The message to display.
 * @param unique Whether to only display the message if the title is unique.
 *
 * @todo Consider making this a static method on singleton {@linkcode MessageContainer}
 */
export function showMessage(message: APIMessage | null, unique = false): void {
    if (!message) {
        return;
    }

    const container = document.querySelector<MessageContainer>("ak-message-container");

    if (!container) {
        throw new SentryIgnoredError("failed to find message container");
    }

    if (!message.message.trim()) {
        console.warn("authentik/messages: `showMessage` received an empty message", message);

        message.message = msg("An unknown error occurred");
        message.description ??= msg("Please check the browser console for more details.");
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
    @state()
    protected messages: APIMessage[] = [];

    @property()
    alignment: "top" | "bottom" = "top";

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
                    .description=${description}
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
