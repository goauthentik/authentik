import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { BaseTaskButton } from "#elements/buttons/SpinnerButton/BaseTaskButton";
import { showMessage } from "#elements/messages/MessageContainer";

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
export class ActionButton<R = unknown> extends BaseTaskButton<R> {
    /**
     * The command to run when the button is pressed. Must return a promise. If the promise is a
     * reject or throw, we process the content of the promise and deliver it to the Notification
     * bus.
     *
     * @attr
     */
    @property({ attribute: false })
    public apiRequest: () => Promise<R> = () => {
        throw new TypeError("No API request defined for ActionButton");
    };

    public override callAction(): Promise<R> {
        return this.apiRequest();
    }

    protected async onError(error: unknown) {
        super.onError(error);
        const parsedError = await parseAPIResponseError(error);

        showMessage({
            level: MessageLevel.error,
            message: pluckErrorDetail(parsedError),
        });
    }
}

export default ActionButton;

declare global {
    interface HTMLElementTagNameMap {
        "ak-action-button": ActionButton;
    }
}
