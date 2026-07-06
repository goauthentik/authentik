import "#elements/messages/Message";

import { APIError, pluckErrorDetail } from "#common/errors/network";
import { APIMessage, MessageLevel } from "#common/messages";
import { tryParsingJSON } from "#common/objects";

import { AKElement } from "#elements/Base";
import { ifPresent } from "#elements/utils/attributes";

import { ConsoleLogger } from "#logger/browser";

import { instanceOfValidationError } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFAlertGroup from "@patternfly/patternfly/components/AlertGroup/alert-group.css";

const logger = ConsoleLogger.prefix("messages");

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

    if (!message.message.trim()) {
        logger.warn("authentik/messages: `showMessage` received an empty message", message);

        message.message = msg("An unknown error occurred");
        message.description ??= msg("Please check the browser console for more details.");
    }

    const container = document.querySelector<MessageContainer>("ak-message-container");

    if (!container) {
        logger.warn("authentik/messages: No message container found in DOM");
        logger.info("authentik/messages: Message to show:", message);

        return;
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
    public static readonly serializedSelector = "script[data-id=authentik-messages]";

    @property({ attribute: false })
    public messages: APIMessage[] = [];

    @property()
    alignment: "top" | "bottom" = "top";

    static styles: CSSResult[] = [
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

        window.addEventListener("ak-message", (event) => {
            this.addMessage(event.message);
        });
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        requestAnimationFrame(this.drainMessages);
    }

    protected drainMessages = (): void => {
        const selector = (this.constructor as typeof MessageContainer).serializedSelector;
        const container = this.ownerDocument.querySelector<HTMLScriptElement>(selector);

        if (!container) {
            logger.warn(`Expected to find a script tag with ${selector}, but none was found.`);
            return;
        }

        const messages = tryParsingJSON<APIMessage[]>(container.textContent);

        if (!messages?.length) {
            return;
        }

        for (const message of messages) {
            this.addMessage(message);
        }
    };

    public addMessage(message: APIMessage, unique?: boolean): boolean {
        if (message.key) {
            this.messages = [...this.messages.filter((m) => m.key !== message.key), message];

            return true;
        }

        if (unique) {
            const match = this.messages.some((m) => m.message === message.message);

            if (match) return false;
        }

        this.messages = [...this.messages, message];

        return true;
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
                const { message: title, description, level, icon } = message;

                return html`<ak-message
                    ?live=${idx === 0}
                    icon=${ifPresent(icon)}
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
