import { CSSResult, LitElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { Table } from "./Table";
import PFModalBox from "@patternfly/patternfly/components/ModalBox/modal-box.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFBackdrop from "@patternfly/patternfly/components/Backdrop/backdrop.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import AKGlobal from "../../authentik.css";
import { PFSize } from "../Spinner";
import { MODAL_BUTTON_STYLES } from "../buttons/ModalButton";

export abstract class TableModal<T> extends Table<T> {
    @property()
    size: PFSize = PFSize.Large;

    @property({ type: Boolean })
    open = false;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFModalBox, PFBullseye, PFContent, PFBackdrop, PFPage, PFStack, AKGlobal, MODAL_BUTTON_STYLES);
    }

    constructor() {
        super();
        window.addEventListener("keyup", (e) => {
            if (e.code === "Escape") {
                this.resetForms();
                this.open = false;
            }
        });
    }

    resetForms(): void {
        this.querySelectorAll<HTMLFormElement>("[slot=form]").forEach(form => {
            form?.resetForm();
        });
    }

    onClick(): void {
        this.open = true;
        this.querySelectorAll("*").forEach(child => {
            if ("requestUpdate" in child) {
                (child as LitElement).requestUpdate();
            }
        });
    }

    renderModalInner(): TemplateResult {
        return this.renderTable();
    }

    renderModal(): TemplateResult {
        return html`<div class="pf-c-backdrop">
            <div class="pf-l-bullseye">
                <div
                    class="pf-c-modal-box ${this.size}"
                    role="dialog"
                    aria-modal="true"
                >
                    <button
                        @click=${() => (this.open = false)}
                        class="pf-c-button pf-m-plain"
                        type="button"
                        aria-label="Close dialog"
                    >
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                    ${this.renderModalInner()}
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        return html` <slot name="trigger" @click=${() => this.onClick()}></slot>
            ${this.open ? this.renderModal() : ""}`;
    }
}
