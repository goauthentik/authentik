import "#elements/buttons/SpinnerButton/index";
import "#elements/entities/UsedByTable";

import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { ModalButton } from "#elements/buttons/ModalButton";
import { BulkDeleteMetadata } from "#elements/entities/UsedByTable";
import { showMessage } from "#elements/messages/MessageContainer";

import { UsedBy } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-forms-delete-bulk")
export class DeleteBulkForm<T> extends ModalButton {
    @property({ attribute: false })
    public objects: T[] = [];

    @property({ type: String, attribute: "object-label" })
    public objectLabel: string | null = null;

    @property({ type: String, attribute: "submit-label" })
    public submitLabel: string | null = null;

    @property({ type: String, attribute: "action-subtext" })
    public actionSubtext: string | null = null;

    @property({ type: String, attribute: "button-label" })
    public buttonLabel = msg("Delete");

    /**
     * Action shown in messages, for example `deleted` or `removed`
     */
    @property({ type: String })
    public action = msg("deleted");

    @property({ attribute: false })
    public metadata: (item: T) => BulkDeleteMetadata[] = (item: T) => {
        const rec = item as Record<string, unknown>;
        const meta: BulkDeleteMetadata[] = [];

        if (Object.hasOwn(rec, "name")) {
            meta.push({ key: msg("Name"), value: rec.name as string });
        }

        if (Object.hasOwn(rec, "pk")) {
            meta.push({ key: msg("ID"), value: rec.pk as string });
        }

        return meta;
    };

    @property({ attribute: false })
    public usedBy?: (item: T) => Promise<UsedBy[]>;

    @property({ attribute: false })
    public delete!: (item: T) => Promise<unknown>;

    protected async confirm(): Promise<void> {
        return Promise.all(this.objects.map((item) => this.delete(item)))
            .then(() => {
                showMessage({
                    message: msg(
                        str`Successfully deleted ${this.objects.length} ${this.objectLabel}`,
                    ),
                    level: MessageLevel.success,
                });

                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );
                this.open = false;
            })
            .catch((parsedError: unknown) => {
                return parseAPIResponseError(parsedError).then(() => {
                    showMessage({
                        message: msg(str`Failed to delete ${this.objectLabel}`),
                        description: pluckErrorDetail(parsedError),
                        level: MessageLevel.error,
                    });
                });
            });
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">
                        ${this.submitLabel
                            ? this.submitLabel
                            : msg(str`Delete ${this.objectLabel}`)}
                    </h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p class="pf-c-title">
                        ${this.actionSubtext
                            ? this.actionSubtext
                            : msg(
                                  str`Are you sure you want to delete ${this.objects.length} ${this.objectLabel}?`,
                              )}
                    </p>
                    <slot name="notice"></slot>
                </form>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <ak-used-by-table
                    .items=${this.objects}
                    .usedBy=${this.usedBy}
                    .metadata=${this.metadata}
                >
                </ak-used-by-table>
            </section>
            <fieldset class="pf-c-modal-box__footer">
                <legend class="sr-only">${msg("Form actions")}</legend>
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-plain"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>

                <ak-spinner-button .callAction=${() => this.confirm()} class="pf-m-danger">
                    ${this.buttonLabel}
                </ak-spinner-button>
            </fieldset>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-delete-bulk": DeleteBulkForm<object>;
    }
}
