import { getCookie } from "./utils.js";
import { updateMessages } from "./Messages.js";
import { customElement, html, LitElement, property } from "lit-element";

const PRIMARY_CLASS = "pf-m-primary";
const SUCCESS_CLASS = "pf-m-success";
const ERROR_CLASS = "pf-m-danger";
const PROGRESS_CLASSES = ["pf-m-progress", "pf-m-in-progress"];

@customElement("pb-action-button")
export class ActionButton extends LitElement {

    constructor() {
        super();
        this.querySelector("button")?.addEventListener('click', e => this.callAction());
    }

    @property()
    url: string = "";

    isRunning = false;

    setLoading() {
        this.isRunning = true;
        this.classList.add(...PROGRESS_CLASSES);
    }

    setDone(statusClass: string) {
        this.isRunning = false;
        this.classList.remove(...PROGRESS_CLASSES);
        this.classList.replace(PRIMARY_CLASS, statusClass);
        // Trigger messages to update
        updateMessages();
        setTimeout(() => {
            this.classList.replace(statusClass, PRIMARY_CLASS);
        }, 1000);
    }

    callAction() {
        if (this.isRunning === true) {
            return;
        }
        this.setLoading();
        const csrftoken = getCookie('passbook_csrf');
        const request = new Request(
            this.url,
            { headers: { 'X-CSRFToken': csrftoken! } }
        );
        fetch(request, {
            method: "POST",
            mode: 'same-origin',
        }).then(r => r.json()).then(r => {
            this.setDone(SUCCESS_CLASS);
        }).catch(() => {
            this.setDone(ERROR_CLASS);
        });
    }

    render() {
        return html`<button class="pf-c-button pf-m-primary">
            ${this.isRunning ? html`
            <span class="pf-c-button__progress">
                <span class="pf-c-spinner pf-m-md" role="progressbar" aria-valuetext="Loading...">
                    <span class="pf-c-spinner__clipper"></span>
                    <span class="pf-c-spinner__lead-ball"></span>
                    <span class="pf-c-spinner__tail-ball"></span>
                </span>
            </span>` : ""}
            <slot></slot>
        </button>`;
    }

}
