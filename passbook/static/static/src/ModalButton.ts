import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import ModalBoxStyle from "@patternfly/patternfly/components/ModalBox/modal-box.css";
// @ts-ignore
import BullseyeStyle from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
// @ts-ignore
import BackdropStyle from "@patternfly/patternfly/components/Backdrop/backdrop.css";
import { updateMessages } from "./Messages";

@customElement("pb-modal-button")
export class ModalButton extends LitElement {

    @property()
    href: string = "";

    @property()
    open: boolean = false;

    static get styles() {
        return [ModalBoxStyle, BullseyeStyle, BackdropStyle]
    }

    constructor() {
        super();
        window.addEventListener("keyup", e => {
            if (e.code === "Escape") {
                this.open = false;
            }
        });
    }

    setContent(content: string) {
        this.querySelector("[slot=modal]")!.innerHTML = content;
        // Ensure links close the modal
        this.querySelectorAll<HTMLAnchorElement>("[slot=modal] a").forEach(a => {
            // Make click on a close the modal
            a.addEventListener("click", e => {
                e.preventDefault();
                this.open = false;
            });
        });
        // Ensure forms sends in AJAX
        this.querySelectorAll<HTMLFormElement>("[slot=modal] form").forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                let formData = new FormData(form);
                fetch((form.action === window.location.toString()) ? this.href : form.action, {
                    method: form.method,
                    body: formData,
                }).then((response) => {
                    return response.text();
                }).then(data => {
                    if (data.indexOf("csrfmiddlewaretoken") !== -1) {
                        this.setContent(data);
                    } else {
                        this.open = false;
                        this.dispatchEvent(new CustomEvent('hashchange', { bubbles: true }));
                        updateMessages();
                    }
                }).catch((e) => {
                    console.error(e);
                });
            });
        });
    }

    onClick(e: MouseEvent) {
        const request = new Request(
            this.href,
        );
        fetch(request, {
            mode: 'same-origin',
        }).then(r => r.text()).then((t) => {
            this.setContent(t);
            this.open = true;
        }).catch(e => {
            console.error(e);
        });
    }

    renderModal() {
        return html`<div class="pf-c-backdrop">
            <div class="pf-l-bullseye">
                <div class="pf-c-modal-box pf-m-md" role="dialog" aria-modal="true" aria-labelledby="modal-md-title" aria-describedby="modal-md-description">
                    <button @click=${() => this.open = false} class="pf-c-button pf-m-plain" type="button" aria-label="Close dialog">
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
