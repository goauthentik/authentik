import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import ModalBoxStyle from "@patternfly/patternfly/components/ModalBox/modal-box.css";
// @ts-ignore
import BullseyeStyle from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
// @ts-ignore
import BackdropStyle from "@patternfly/patternfly/components/Backdrop/backdrop.css";
// @ts-ignore
import ButtonStyle from "@patternfly/patternfly/components/Button/button.css";
// @ts-ignore
import fa from "@fortawesome/fontawesome-free/css/solid.css";

import { convertToSlug } from "../../utils";
import { SpinnerButton } from "./SpinnerButton";
import { PRIMARY_CLASS } from "../../constants";
import { showMessage } from "../messages/MessageContainer";

@customElement("ak-modal-button")
export class ModalButton extends LitElement {
    @property()
    href?: string;

    @property({type: Boolean})
    open = false;

    static get styles(): CSSResult[] {
        return [
            css`
                :host {
                    text-align: left;
                }
                ::slotted(*) {
                    overflow-y: auto;
                }
            `,
            ModalBoxStyle,
            BullseyeStyle,
            BackdropStyle,
            ButtonStyle,
            fa,
        ];
    }

    constructor() {
        super();
        window.addEventListener("keyup", (e) => {
            if (e.code === "Escape") {
                this.open = false;
            }
        });
    }

    updateHandlers(): void {
        // Ensure links close the modal
        this.querySelectorAll<HTMLAnchorElement>("[slot=modal] a").forEach((a) => {
            if (a.target == "_blank") {
                return;
            }
            // Make click on a close the modal
            a.addEventListener("click", (e) => {
                e.preventDefault();
                this.open = false;
            });
        });
        // Make name field update slug field
        this.querySelectorAll<HTMLInputElement>("input[name=name]").forEach((input) => {
            input.addEventListener("input", () => {
                const form = input.closest("form");
                if (form === null) {
                    return;
                }
                const slugField = form.querySelector<HTMLInputElement>("input[name=slug]");
                if (!slugField) {
                    return;
                }
                slugField.value = convertToSlug(input.value);
            });
        });
        // Ensure forms sends in AJAX
        this.querySelectorAll<HTMLFormElement>("[slot=modal] form").forEach((form) => {
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                fetch(this.href ? this.href : form.action, {
                    method: form.method,
                    body: formData,
                    redirect: "manual",
                })
                    .then((response) => {
                        return response.text();
                    })
                    .then((data) => {
                        if (data.indexOf("csrfmiddlewaretoken") !== -1) {
                            const modalSlot = this.querySelector("[slot=modal]");
                            if (!modalSlot) {
                                console.debug("authentik/modalbutton: modal slot not found?");
                                return;
                            }
                            modalSlot.innerHTML = data;
                            console.debug("authentik/modalbutton: re-showing form");
                            this.updateHandlers();
                        } else {
                            this.open = false;
                            console.debug("authentik/modalbutton: successful submit");
                            this.dispatchEvent(
                                new CustomEvent("ak-refresh", {
                                    bubbles: true,
                                    composed: true,
                                })
                            );
                        }
                    })
                    .catch((e) => {
                        showMessage({
                            level_tag: "error",
                            message: "Unexpected error"
                        });
                        console.log(e);
                    });
            });
        });
    }

    onClick(): void {
        if (!this.href) {
            this.updateHandlers();
            this.open = true;
        } else {
            const request = new Request(this.href);
            fetch(request, {
                mode: "same-origin",
            })
                .then((r) => r.text())
                .then((t) => {
                    const modalSlot = this.querySelector("[slot=modal]");
                    if (!modalSlot) {
                        return;
                    }
                    modalSlot.innerHTML = t;
                    this.updateHandlers();
                    this.open = true;
                    this.querySelectorAll<SpinnerButton>("ak-spinner-button").forEach((sb) => {
                        sb.setDone(PRIMARY_CLASS);
                    });
                })
                .catch((e) => {
                    showMessage({
                        level_tag: "error",
                        message: "Unexpected error"
                    });
                    console.log(e);
                });
        }
    }

    renderModal(): TemplateResult {
        return html`<div class="pf-c-backdrop">
            <div class="pf-l-bullseye">
                <div
                    class="pf-c-modal-box pf-m-lg"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="modal-md-title"
                    aria-describedby="modal-md-description"
                >
                    <button
                        @click=${() => (this.open = false)}
                        class="pf-c-button pf-m-plain"
                        type="button"
                        aria-label="Close dialog"
                    >
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                    <slot name="modal"> </slot>
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        return html` <slot name="trigger" @click=${() => this.onClick()}></slot>
            ${this.open ? this.renderModal() : ""}`;
    }
}
