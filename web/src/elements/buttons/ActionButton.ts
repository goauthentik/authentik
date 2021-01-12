import { getCookie } from "../../utils";
import { customElement, property } from "lit-element";
import { ERROR_CLASS, SUCCESS_CLASS } from "../../constants";
import { SpinnerButton } from "./SpinnerButton";
import { showMessage } from "../messages/MessageContainer";

@customElement("ak-action-button")
export class ActionButton extends SpinnerButton {
    @property()
    url = "";

    callAction(): void {
        if (this.isRunning === true) {
            return;
        }
        this.setLoading();
        const csrftoken = getCookie("authentik_csrf");
        if (!csrftoken) {
            console.debug("No csrf token in cookie");
            this.setDone(ERROR_CLASS);
            return;
        }
        const request = new Request(this.url, {
            headers: { "X-CSRFToken": csrftoken },
        });
        fetch(request, {
            method: "POST",
            mode: "same-origin",
        })
            .then((r) => {
                if (!r.ok) {
                    throw r;
                }
                return r;
            })
            .then((r) => r.json())
            .then(() => {
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
