import { MessageLevel } from "@goauthentik/common/messages";
import { BaseTaskButton } from "@goauthentik/elements/buttons/SpinnerButton/BaseTaskButton";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";

import { customElement, property } from "lit/decorators.js";

/**
 * A button associated with an event handler for loading data. Takes an asynchronous function as its
 * only property.
 *
 * @element ak-action-button
 *
 * @slot - The label for the button
 *
 * @fires ak-button-click - When the button is first clicked.
 * @fires ak-button-success - When the async process succeeds
 * @fires ak-button-failure - When the async process fails
 * @fires ak-button-reset - When the button is reset after the async process completes
 */

@customElement("ak-action-button")
export class ActionButton extends BaseTaskButton {
    /**
     * The command to run when the button is pressed. Must return a promise. If the promise is a
     * reject or throw, we process the content of the promise and deliver it to the Notification
     * bus.
     *
     * @attr
     */

    @property({ attribute: false })
    apiRequest: () => Promise<unknown> = () => {
        throw new Error();
    };

    constructor() {
        super();
        this.onError = this.onError.bind(this);
    }

    callAction = (): Promise<unknown> => {
        return this.apiRequest();
    };

    async onError(error: Error | Response) {
        super.onError(error);
        const message = error instanceof Error ? error.toString() : await error.text();
        showMessage({
            level: MessageLevel.error,
            message,
        });
    }
}

export default ActionButton;
