import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { ModalButton } from "../buttons/ModalButton";

@customElement("ak-forms-delete")
export class DeleteForm extends ModalButton {

    @property({attribute: false})
    obj?: Record<string, unknown>;

    @property()
    objectLabel?: string;

    @property({attribute: false})
    delete!: () => Promise<void>;

    confirm(): void {
        this.delete().then(() => {
            this.open = false;
            this.dispatchEvent(
                new CustomEvent("ak-refresh", {
                    bubbles: true,
                    composed: true,
                })
            );
        });
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
            <div class="pf-c-content">
                <h1 class="pf-c-title pf-m-2xl">
                    ${gettext(`Delete ${this.objectLabel}`)}
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
                                        `Are you sure you want to delete ${this.objectLabel} '${this.obj?.name}'?`
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
                class="pf-m-danger">
                ${gettext("Delete")}
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
