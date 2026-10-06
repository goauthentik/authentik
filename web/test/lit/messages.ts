import { APIMessage } from "#common/messages";

import { MessageContainer } from "#elements/messages/MessageContainer";

import { vi } from "vitest";

export interface CapturedMessages {
    /** Every message shown since capture began, oldest first. */
    messages: APIMessage[];
    /** Removes the stand-in elements. Spies are left to `vi.restoreAllMocks()`. */
    cleanup: () => void;
}

/**
 * Capture the toasts a component shows when it is rendered outside an app.
 *
 * `showMessage` looks up the interface root, then the `<ak-message-container>`
 * it draws into, and throws when there is no root. This stands in for both:
 * an interface root with no dialogs open, and a message container whose
 * `addMessage` records instead of rendering.
 */
export function captureMessages(): CapturedMessages {
    const messages: APIMessage[] = [];

    vi.spyOn(MessageContainer.prototype, "addMessage").mockImplementation((message) => {
        messages.push(message);

        return true;
    });

    const interfaceRoot = Object.assign(document.createElement("div"), {
        id: "interface-root",
        renderRoot: document.createDocumentFragment(),
    });

    const container = document.createElement("ak-message-container");

    document.body.append(interfaceRoot, container);

    return {
        messages,
        cleanup: () => {
            interfaceRoot.remove();
            container.remove();
        },
    };
}
