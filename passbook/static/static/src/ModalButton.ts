import { customElement, html, LitElement, property } from "lit-element";

const PRIMARY_CLASS = "pf-m-primary";
const SUCCESS_CLASS = "pf-m-success";
const ERROR_CLASS = "pf-m-danger";
const PROGRESS_CLASSES = ["pf-m-progress", "pf-m-in-progress"];

@customElement("pb-modal-button")
export class ModalButton extends LitElement {

    @property()
    href: string = "";

    constructor() {
        super();
        this.addEventListener('click', e => this.callAction(e));
    }

    getModal() {
        return html`<div class="pf-c-backdrop">
            <div class="pf-l-bullseye">
                <div class="pf-c-modal-box pf-m-md" role="dialog" aria-modal="true" aria-labelledby="modal-md-title" aria-describedby="modal-md-description">
                <button class="pf-c-button pf-m-plain" type="button" aria-label="Close dialog">
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>

                <header class="pf-c-modal-box__header">
                    <h1 class="pf-c-modal-box__title" id="modal-md-title">This is a long header title that will truncate because modal titles should be very short. Use the modal body to provide more info.</h1>
                </header>
                <div class="pf-c-modal-box__body">
                    <p id="modal-md-description">The "aria-describedby" attribute can be applied to any text that adequately describes the modal's purpose. It does not have to be assigned to ".pf-c-modal-box__body"</p>
                    <p>Form here</p>
                </div>
                <footer class="pf-c-modal-box__footer">
                    <button class="pf-c-button pf-m-primary" type="button">Save</button>
                    <button class="pf-c-button pf-m-link" type="button">Cancel</button>
                </footer>
                </div>
            </div>
        </div>`;
    }

    callAction(e: MouseEvent) {
        e.preventDefault();
        const request = new Request(
            this.href,
        );
        fetch(request, {
            method: "POST",
            mode: 'same-origin',
        }).then(r => {
            // this.
        }).catch(() => {
            // this.setDone(ERROR_CLASS);
        });
    }

}
