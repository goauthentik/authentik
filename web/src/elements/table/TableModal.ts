import { SlottedTemplateResult } from "../types.js";

import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import { MODAL_BUTTON_STYLES } from "#elements/buttons/ModalButton";
import { ModalShowEvent } from "#elements/controllers/ModalOrchestrationController";
import type { Form } from "#elements/forms/Form";
import { Table } from "#elements/table/Table";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
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
    public set open(nextValue: boolean) {
        this.#open = nextValue;

        if (nextValue) {
            this.fetch();
        }
    }

    public get open(): boolean {
        return this.#open;
    }

    #open = false;

    public static override styles: CSSResult[] = [
        ...super.styles,
        PFModalBox,
        PFBullseye,
        PFContent,
        PFBackdrop,
        PFPage,
        PFStack,
        MODAL_BUTTON_STYLES,
    ];

    public override async fetch(): Promise<void> {
        if (!this.open) {
            return;
        }

        return super.fetch();
    }

    public close = () => {
        this.resetForms();
        this.open = false;
    };

    protected resetForms(): void {
        for (const form of this.querySelectorAll<Form | HTMLFormElement>("[slot=form]")) {
            form.reset?.();
        }
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
    protected renderModalInner(): TemplateResult {
        return this.renderTable();
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
                    ${this.renderModalInner()}
                </div>
            </div>
        </div>`;
    }

    public override render(): TemplateResult {
        return html` <slot name="trigger" @click=${this.show}></slot>
            ${this.open ? this.renderModal() : nothing}`;
    }
}
