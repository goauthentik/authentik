import { getCookie } from "../../utils";
import { customElement, property } from "lit-element";
import { ERROR_CLASS, SUCCESS_CLASS } from "../../constants";
import { SpinnerButton } from "./SpinnerButton";

@customElement("pb-action-button")
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
            .then((r) => r.json())
            .then(() => {
                this.setDone(SUCCESS_CLASS);
            })
            .catch(() => {
                this.setDone(ERROR_CLASS);
            });
    }
}
