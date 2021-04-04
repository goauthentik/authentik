import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { EVENT_REFRESH } from "../../constants";
import { ModalButton } from "../buttons/ModalButton";
import { MessageLevel } from "../messages/Message";
import { showMessage } from "../messages/MessageContainer";
import "../buttons/SpinnerButton";

@customElement("ak-forms-delete")
export class DeleteForm extends ModalButton {

    @property({attribute: false})
    obj?: Record<string, unknown>;

    @property()
    objectLabel?: string;

    @property({attribute: false})
    delete!: () => Promise<unknown>;

    confirm(): void {
        this.delete().then(() => {
            this.onSuccess();
            this.open = false;
            this.dispatchEvent(
                new CustomEvent(EVENT_REFRESH, {
                    bubbles: true,
                    composed: true,
                })
            );
        }).catch((e) => {
            this.onError(e);
        });
    }

    onSuccess(): void {
        showMessage({
            message: t`Successfully deleted ${this.objectLabel} ${ this.obj?.name }`,
            level: MessageLevel.success,
        });
    }

    onError(e: Error): void {
        showMessage({
            message: t`Failed to delete ${this.objectLabel}: ${e.toString()}`,
            level: MessageLevel.error,
        });
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
            <div class="pf-c-content">
                <h1 class="pf-c-title pf-m-2xl">
                    ${t`Delete ${this.objectLabel}`}
                </h1>
            </div>
        </section>
        <section class="pf-c-page__main-section pf-m-light">
            <form class="pf-c-form pf-m-horizontal">
                <p>
                    ${t`Are you sure you want to delete ${this.objectLabel} '${this.obj?.name}'?`}
                </p>
            </form>
        </section>
        <footer class="pf-c-modal-box__footer">
            <ak-spinner-button
                .callAction=${() => {
                    this.confirm();
                }}
                class="pf-m-danger">
                ${t`Delete`}
            </ak-spinner-button>&nbsp;
            <ak-spinner-button
                .callAction=${() => {
                    this.open = false;
                }}
                class="pf-m-secondary">
                ${t`Cancel`}
            </ak-spinner-button>
        </footer>`;
    }

}
