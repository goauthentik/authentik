import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import "../../elements/buttons/SpinnerButton";
import { DeleteForm } from "../../elements/forms/DeleteForm";
import { MessageLevel } from "../../elements/messages/Message";
import { showMessage } from "../../elements/messages/MessageContainer";

@customElement("ak-user-active-form")
export class UserActiveForm extends DeleteForm {
    onSuccess(): void {
        showMessage({
            message: t`Successfully updated ${this.objectLabel} ${this.obj?.name}`,
            level: MessageLevel.success,
        });
    }

    onError(e: Error): void {
        showMessage({
            message: t`Failed to update ${this.objectLabel}: ${e.toString()}`,
            level: MessageLevel.error,
        });
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${t`Update ${this.objectLabel}`}</h1>
                </div>
            </section>
            <section class="pf-c-page__main-section pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p>
                        ${t`Are you sure you want to update ${this.objectLabel} "${this.obj?.name}"?`}
                    </p>
                </form>
            </section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm();
                    }}
                    class="pf-m-warning"
                >
                    ${t`Update`} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${t`Cancel`}
                </ak-spinner-button>
            </footer>`;
    }
}
