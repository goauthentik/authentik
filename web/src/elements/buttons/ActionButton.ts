import { MessageLevel } from "@goauthentik/web/elements/messages/Message";
import { showMessage } from "@goauthentik/web/elements/messages/MessageContainer";

import { customElement, property } from "lit/decorators.js";

import { SpinnerButton } from "./SpinnerButton";

@customElement("ak-action-button")
export class ActionButton extends SpinnerButton {
    @property({ attribute: false })
    apiRequest: () => Promise<unknown> = () => {
        throw new Error();
    };

    callAction = (): Promise<unknown> => {
        this.setLoading();
        return this.apiRequest().catch((e: Error | Response) => {
            if (e instanceof Error) {
                showMessage({
                    level: MessageLevel.error,
                    message: e.toString(),
                });
            } else {
                e.text().then((t) => {
                    showMessage({
                        level: MessageLevel.error,
                        message: t,
                    });
                });
            }
        });
    };
}
