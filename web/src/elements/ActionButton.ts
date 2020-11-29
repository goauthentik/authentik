import { getCookie } from "../utils";
import { customElement, html, property } from "lit-element";
import { ERROR_CLASS, SUCCESS_CLASS } from "../constants";
import { SpinnerButton } from "./SpinnerButton";

@customElement("pb-action-button")
export class ActionButton extends SpinnerButton {
    @property()
    url: string = "";

    callAction() {
        if (this.isRunning === true) {
            return;
        }
        this.setLoading();
        const csrftoken = getCookie("passbook_csrf");
        const request = new Request(this.url, {
            headers: { "X-CSRFToken": csrftoken! },
        });
        fetch(request, {
            method: "POST",
            mode: "same-origin",
        })
            .then((r) => r.json())
            .then((r) => {
                this.setDone(SUCCESS_CLASS);
            })
            .catch(() => {
                this.setDone(ERROR_CLASS);
            });
    }
}
