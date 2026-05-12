import "#elements/messages/Message";

import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { APIMessage, MessageLevel } from "#common/messages";

import { AKElement } from "#elements/Base";
import Styles from "#elements/messages/styles.css";
import { ifPresent } from "#elements/utils/attributes";
import { findTopmost } from "#elements/utils/render-roots";

import { ConsoleLogger } from "#logger/browser";

import { instanceOfValidationError } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, PropertyValues } from "lit";
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
export function showMessage(message: APIMessage | null, unique: boolean = false): boolean {
    if (!message) {
        return false;
    }

    if (!message.message.trim()) {
        logger.warn("authentik/messages: `showMessage` received an empty message", message);

        message.message = msg("An unknown error occurred");
        message.description ??= msg("Please check the browser console for more details.");
    }

    const topmost = findTopmost();

    const container = topmost.querySelector<MessageContainer>("ak-message-container");

    if (!container) {
        logger.warn("authentik/messages: No message container found in DOM");
        logger.info("authentik/messages: Message to show:", message);

        return false;
    }

    container.addMessage(message, unique);
    container.requestUpdate();

    return true;
}

/**
 * Given an API error, display the error(s) to the user.
 *
 * @param error The API error to display.
 * @param unique Whether to only display the message if the title is unique.
 * @see {@link parseAPIResponseError} for more information on how to handle API errors.
 */
export function showAPIErrorMessage(error: unknown, unique = false): Promise<void> {
    if (!error) {
        return Promise.resolve();
    }

    if (
        typeof error === "object" &&
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

        return Promise.resolve();
    }

    return parseAPIResponseError(error)
        .then((parsedError) => pluckErrorDetail(parsedError))
        .catch(() => pluckErrorDetail(error, msg("An unknown error occurred")))
        .then((message) => {
            showMessage(
                {
                    level: MessageLevel.error,
                    message: message,
                },
                unique,
            );
        });
}

export type MessageContainerAlignment = "top-left" | "top-right" | "bottom-left" | "bottom-right";

@customElement("ak-message-container")
export class MessageContainer extends AKElement {
    @property({ attribute: false })
    public messages: APIMessage[] = [];

    @property({ type: String, reflect: true, useDefault: true })
    public alignment: MessageContainerAlignment = "bottom-right";

    static styles: CSSResult[] = [PFAlertGroup, Styles];

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

        this.popover = "manual";
    }

    public updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        if (changedProperties.has("messages") && this.messages.length) {
            // Invoking the popover is only needed for browsers that support dialogs
            // that support HTMLDialogElement.showModal()
            const source = findTopmost(this.ownerDocument);

            this.showPopover?.({ source });
        }
    }

    public addMessage(message: APIMessage, unique?: boolean): boolean {
        if (message.key) {
            this.messages = [...this.messages.filter((m) => m.key !== message.key), message];

            return true;
        }

        if (unique) {
            const existing = this.messages.find((m) => m.message === message.message);

            if (existing) {
                return false;
            }
        }

        this.messages = [...this.messages, message];

        return true;
    }

    #removeMessage = (message: APIMessage) => {
        this.messages = this.messages.filter((v) => v !== message);

        if (this.messages.length === 0) {
            // Just the same, hide the popover for browsers that support native dialogs.
            this.hidePopover?.();
        }
    };

    render() {
        return html`<ul
            role="region"
            part="messages"
            aria-label="${msg("Status messages")}"
            class="pf-c-alert-group pf-m-toast"
            data-alignment=${this.alignment}
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
