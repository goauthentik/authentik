import { SlottedTemplateResult } from "#elements/types";
import { PFSize } from "@goauthentik/common/enums.js";
import { AKElement } from "@goauthentik/elements/Base";
import { MODAL_BUTTON_STYLES } from "@goauthentik/elements/buttons/ModalButton";
import { ModalShowEvent } from "@goauthentik/elements/controllers/ModalOrchestrationController.js";
import { Table } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { CSSResult, nothing } from "lit";
import { TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import PFBackdrop from "@patternfly/patternfly/components/Backdrop/backdrop.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFModalBox from "@patternfly/patternfly/components/ModalBox/modal-box.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";

export abstract class TableModal<T extends object> extends Table<T> {
    @property()
    public size: PFSize = PFSize.Large;

    @property({ type: Boolean })
    set open(nextValue: boolean) {
        this.#open = nextValue;

        if (nextValue) {
            this.fetch();
        }
    }

    get open(): boolean {
        return this.#open;
    }

    #open = false;

    static styles: CSSResult[] = [
        ...super.styles,
        PFModalBox,
        PFBullseye,
        PFContent,
        PFBackdrop,
        PFPage,
        PFStack,
        MODAL_BUTTON_STYLES,
    ];

    public async fetch(): Promise<void> {
        if (!this.open) {
            return;
        }
        return super.fetch();
    }

    public close = () => {
        this.resetForms();
        this.open = false;
    };

    resetForms(): void {
        this.querySelectorAll<HTMLFormElement>("[slot=form]").forEach((form) => {
            if ("resetForm" in form) {
                form?.resetForm();
            }
        });
    }

    public show = () => {
        this.open = true;
        this.dispatchEvent(new ModalShowEvent(this));

        this.querySelectorAll("*").forEach((child) => {
            if ("requestUpdate" in child) {
                (child as AKElement).requestUpdate();
            }
        });
    };

    #closeListener = () => {
        this.open = false;
    };

    #backdropListener(event: PointerEvent) {
        event.stopPropagation();
    }

    /**
     * @abstract
     */
    protected renderModal(): SlottedTemplateResult {
        return html`<div class="pf-c-backdrop" @click=${this.#backdropListener}>
            <div class="pf-l-bullseye">
                <div class="pf-c-modal-box ${this.size}" role="dialog" aria-modal="true">
                    <button
                        @click=${this.#closeListener}
                        class="pf-c-button pf-m-plain"
                        type="button"
                        aria-label=${msg("Close dialog")}
                    >
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                    ${this.renderTable()}
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        return html` <slot name="trigger" @click=${this.show}></slot>
            ${this.open ? this.renderModal() : nothing}`;
    }
}
