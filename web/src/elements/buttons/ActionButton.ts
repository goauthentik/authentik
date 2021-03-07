import { customElement, property } from "lit-element";
import { ERROR_CLASS, SUCCESS_CLASS } from "../../constants";
import { SpinnerButton } from "./SpinnerButton";
import { showMessage } from "../messages/MessageContainer";

@customElement("ak-action-button")
export class ActionButton extends SpinnerButton {
    @property()
    url = "";

    @property()
    method = "POST";

    @property({attribute: false})
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiRequest(): Promise<any> {
        throw new Error();
    }

    callAction(): void {
        if (this.isRunning === true) {
            return;
        }
        this.setLoading();
        this.apiRequest().then(() => {
            this.setDone(SUCCESS_CLASS);
        })
        .catch((e: Error | Response) => {
            if (e instanceof Error) {
                showMessage({
                    level_tag: "error",
                    message: e.toString()
                });
            } else {
                e.text().then(t => {
                    showMessage({
                        level_tag: "error",
                        message: t
                    });
                });
            }
            this.setDone(ERROR_CLASS);
        });
    }
}
