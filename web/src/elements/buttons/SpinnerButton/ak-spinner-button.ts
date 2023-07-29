import { customElement } from "lit/decorators.js";
import { property } from "lit/decorators.js";

import { BaseTaskButton } from "./BaseTaskButton";

/**
 * A button associated with an event handler for loading data. Takes an asynchronous function as its
 * only property.
 *
 * @element ak-spinner-button
 *
 * @slot - The label for the button
 *
 * @fires ak-button-click - When the button is first clicked.
 * @fires ak-button-success - When the async process succeeds
 * @fires ak-button-failure - When the async process fails
 * @fires ak-button-reset - When the button is reset after the async process completes
 */

@customElement("ak-spinner-button")
export class SpinnerButton extends BaseTaskButton {
    /**
     * The command to run when the button is pressed. Must return a promise. We don't do anything
     * with that promise other than check if it's a resolve or reject, and rethrow the event after.
     *
     * @attr
     */
    @property({ type: Object, attribute: false })
    callAction!: () => Promise<unknown>;
}

export default SpinnerButton;
