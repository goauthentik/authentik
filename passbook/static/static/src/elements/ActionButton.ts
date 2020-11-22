import { getCookie } from "../utils";
import { updateMessages } from "./Messages";
import { customElement, html, LitElement, property } from "lit-element";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
// @ts-ignore
import ButtonStyle from "@patternfly/patternfly/components/Button/button.css";
// @ts-ignore
import SpinnerStyle from "@patternfly/patternfly/components/Spinner/spinner.css";

const PRIMARY_CLASS = "pf-m-primary";
const SUCCESS_CLASS = "pf-m-success";
const ERROR_CLASS = "pf-m-danger";
const PROGRESS_CLASS ="pf-m-in-progress";

@customElement("pb-action-button")
export class ActionButton extends LitElement {

    @property()
    url: string = "";

    @property()
    isRunning = false;

    static get styles() {
        return [GlobalsStyle, ButtonStyle, SpinnerStyle]
    }

    setLoading() {
        this.isRunning = true;
        this.classList.add(PROGRESS_CLASS);
        this.requestUpdate();
    }

    setDone(statusClass: string) {
        this.isRunning = false;
        this.classList.remove(PROGRESS_CLASS);
        this.classList.replace(PRIMARY_CLASS, statusClass);
        this.requestUpdate();
        // Trigger messages to update
        updateMessages();
        setTimeout(() => {
            this.classList.replace(statusClass, PRIMARY_CLASS);
            this.requestUpdate();
        }, 1000);
    }

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

    render() {
        return html`<button class="pf-c-button pf-m-progress ${this.classList}" @click=${() => this.callAction()}>
            ${this.isRunning
                ? html` <span class="pf-c-button__progress">
                      <span
                          class="pf-c-spinner pf-m-md"
                          role="progressbar"
                          aria-valuetext="Loading..."
                      >
                          <span class="pf-c-spinner__clipper"></span>
                          <span class="pf-c-spinner__lead-ball"></span>
                          <span class="pf-c-spinner__tail-ball"></span>
                      </span>
                  </span>`
                : ""}
            <slot></slot>
        </button>`;
    }
}
