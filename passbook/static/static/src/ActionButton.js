import { getCookie } from "./utils.js";

const PRIMARY_CLASS = "pf-m-primary";
const SUCCESS_CLASS = "pf-m-success";
const ERROR_CLASS = "pf-m-danger";
const PROGRESS_CLASSES = ["pf-m-progress", "pf-m-in-progress"];

class ActionButton extends HTMLButtonElement {

    constructor() {
        super();
        this.addEventListener('click', e => this.callAction());
    }

    isRunning = false;
    oldBody = "";

    setLoading() {
        this.classList.add(...PROGRESS_CLASSES);
        this.oldBody = this.innerText;
        this.innerHTML = `<span class="pf-c-button__progress">
            <span class="pf-c-spinner pf-m-md" role="progressbar" aria-valuetext="Loading...">
                <span class="pf-c-spinner__clipper"></span>
                <span class="pf-c-spinner__lead-ball"></span>
                <span class="pf-c-spinner__tail-ball"></span>
            </span>
        </span>${this.oldBody}`;
    }

    setDone(statusClass) {
        this.isRunning = false;
        this.classList.remove(...PROGRESS_CLASSES);
        this.innerText = this.oldBody;
        this.classList.replace(PRIMARY_CLASS, statusClass);
        setTimeout(() => {
            console.log('test');
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
            this.attributes["url"].value,
            { headers: { 'X-CSRFToken': csrftoken } }
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

}

customElements.define('action-button', ActionButton, { extends: 'button' });
