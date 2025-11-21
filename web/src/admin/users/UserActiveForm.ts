import "#elements/buttons/SpinnerButton/index";

import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { UserDeleteForm } from "#elements/user/utils";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-active-form")
export class UserActiveForm extends UserDeleteForm {
    onSuccess(): void {
        showMessage({
            message: msg(
                str`Successfully updated ${this.objectLabel} ${this.getObjectDisplayName()}`,
            ),
            level: MessageLevel.success,
        });
    }

    onError(error: unknown): Promise<void> {
        return parseAPIResponseError(error).then((parsedError) => {
            showMessage({
                message: msg(
                    str`Failed to update ${this.objectLabel}: ${pluckErrorDetail(parsedError)}`,
                ),
                level: MessageLevel.error,
            });
        });
    }

    override renderModalInner(): TemplateResult {
        const objName = this.getFormattedObjectName();
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${msg(str`Update ${this.objectLabel}`)}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p>
                        ${msg(str`Are you sure you want to update ${this.objectLabel}${objName}?`)}
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
                    ${msg("Update")} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-active-form": UserActiveForm;
    }
}
