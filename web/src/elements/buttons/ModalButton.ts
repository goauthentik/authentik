import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { unsafeHTML } from "lit-html/directives/unsafe-html";

import { convertToSlug } from "../../utils";
import { SpinnerButton } from "./SpinnerButton";
import { PRIMARY_CLASS } from "../../constants";
import { showMessage } from "../messages/MessageContainer";
import { COMMON_STYLES } from "../../common/styles";

@customElement("ak-modal-button")
export class ModalButton extends LitElement {
    @property()
    href?: string;

    @property({type: Boolean})
    open = false;

    @property()
    modal = "";

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
            css`
                :host {
                    text-align: left;
                }
                ::slotted(*) {
                    overflow-y: auto;
                }
                .pf-c-page__main-section {
                    margin-right: 0;
                }
            `
        );
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
        this.shadowRoot?.querySelectorAll<HTMLAnchorElement>("a").forEach((a) => {
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
        this.shadowRoot?.querySelectorAll<HTMLInputElement>("input[name=name]").forEach((input) => {
            const form = input.closest("form");
            if (form === null) {
                return;
            }
            const slugField = form.querySelector<HTMLInputElement>("input[name=slug]");
            if (!slugField) {
                return;
            }
            // Only attach handler if the slug is already equal to the name
            // if not, they are probably completely different and shouldn't update
            // each other
            if (convertToSlug(input.value) !== slugField.value) {
                return;
            }
            input.addEventListener("input", () => {
                slugField.value = convertToSlug(input.value);
            });
        });
        // Ensure forms sends in AJAX
        this.shadowRoot?.querySelectorAll<HTMLFormElement>("form").forEach((form) => {
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
                    .then((responseData) => {
                        if (responseData.indexOf("csrfmiddlewaretoken") !== -1) {
                            this.modal = responseData;
                            console.debug("authentik/modalbutton: re-showing form");
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
                .then((response) => response.text())
                .then((responseData) => {
                    this.modal = responseData;
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
                    ${unsafeHTML(this.modal)}
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        return html` <slot name="trigger" @click=${() => this.onClick()}></slot>
            ${this.open ? this.renderModal() : ""}`;
    }

    updated(): void {
        this.updateHandlers();
    }
}
