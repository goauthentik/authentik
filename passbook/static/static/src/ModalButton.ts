import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import ModalBoxStyle from "@patternfly/patternfly/components/ModalBox/modal-box.css";
// @ts-ignore
import BullseyeStyle from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
// @ts-ignore
import BackdropStyle from "@patternfly/patternfly/components/Backdrop/backdrop.css";

const PRIMARY_CLASS = "pf-m-primary";
const SUCCESS_CLASS = "pf-m-success";
const ERROR_CLASS = "pf-m-danger";
const PROGRESS_CLASSES = ["pf-m-progress", "pf-m-in-progress"];

@customElement("pb-modal-button")
export class ModalButton extends LitElement {

    @property()
    href: string = "";

    @property()
    open: boolean = false;

    static get styles() {
        return [ModalBoxStyle, BullseyeStyle, BackdropStyle]
    }

    onClick(e: MouseEvent) {
        const request = new Request(
            this.href,
        );
        fetch(request, {
            mode: 'same-origin',
        }).then(r => r.text()).then((t) => {
            this.querySelector("[slot=modal]")!.innerHTML = t;
            // Ensure links close the modal
            this.querySelectorAll<HTMLAnchorElement>("[slot=modal] a").forEach(a => {
                // Make click on a close the modal
                a.addEventListener("click", e => {
                    this.open = false;
                });
            });
            // Ensure input type submit submits the form without reloading the page
            this.querySelectorAll<HTMLInputElement>("[slot=modal] input[type=submit]").forEach(i => {
                i.form?.addEventListener("submit", e => {
                    e.preventDefault();
                    return false;
                });
                i.addEventListener("click", e => {
                    console.log("on submit");
                    e.preventDefault();
                    i.form?.submit();
                    this.open = false;
                });
            });
            this.open = true;
        }).catch(e => {
            console.error(e);
        });
    }

    renderModal() {
        return html`<div class="pf-c-backdrop">
            <div class="pf-l-bullseye">
                <div class="pf-c-modal-box pf-m-md" role="dialog" aria-modal="true" aria-labelledby="modal-md-title" aria-describedby="modal-md-description">
                    <button class="pf-c-button pf-m-plain" type="button" aria-label="Close dialog">
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                    <slot name="modal">
                    </slot>
                </div>
            </div>
        </div>`;
    }

    render() {
        return html`
            <slot name="trigger" @click=${(e: any) => this.onClick(e)}></slot>
            ${this.open ? this.renderModal() : ""}`;
    }

}
