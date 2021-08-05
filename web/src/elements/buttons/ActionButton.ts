import { customElement, property } from "lit-element";
import { SpinnerButton } from "./SpinnerButton";
import { showMessage } from "../messages/MessageContainer";
import { MessageLevel } from "../messages/Message";

@customElement("ak-action-button")
export class ActionButton extends SpinnerButton {

    @property({ attribute: false })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiRequest: () => Promise<any> = () => {
        throw new Error();
    };

    callAction = (): Promise<void> => {
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
            throw e;
        });
    };
}
