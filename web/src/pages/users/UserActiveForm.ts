import { gettext } from "django";
import { customElement, html, TemplateResult } from "lit-element";
import { DeleteForm } from "../../elements/forms/DeleteForm";
import { MessageLevel } from "../../elements/messages/Message";
import { showMessage } from "../../elements/messages/MessageContainer";

@customElement("ak-user-active-form")
export class UserActiveForm extends DeleteForm {

    onSuccess(): void {
        showMessage({
            message: gettext(`Successfully updated ${this.objectLabel} ${this.obj?.name}`),
            level: MessageLevel.success,
        });
    }

    onError(e: Error): void {
        showMessage({
            message: gettext(`Failed to update ${this.objectLabel}: ${e.toString()}`),
            level: MessageLevel.error,
        });
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
            <div class="pf-c-content">
                <h1 class="pf-c-title pf-m-2xl">
                    ${gettext(`Update ${this.objectLabel}`)}
                </h1>
            </div>
        </section>
        <section class="pf-c-page__main-section">
            <div class="pf-l-stack">
                <div class="pf-l-stack__item">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <form class="pf-c-form pf-m-horizontal">
                                <p>
                                    ${gettext(
                                        `Are you sure you want to update ${this.objectLabel} '${this.obj?.name}'?`
                                    )}
                                </p>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <footer class="pf-c-modal-box__footer">
            <ak-spinner-button
                .callAction=${() => {
                    this.confirm();
                }}
                class="pf-m-warning">
                ${gettext("Update")}
            </ak-spinner-button>&nbsp;
            <ak-spinner-button
                .callAction=${() => {
                    this.open = false;
                }}
                class="pf-m-secondary">
                ${gettext("Cancel")}
            </ak-spinner-button>
        </footer>`;
    }

}
