import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

import { UsedBy, UsedByActionEnum } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { EVENT_REFRESH } from "../../constants";
import { PFSize } from "../Spinner";
import { ModalButton } from "../buttons/ModalButton";
import "../buttons/SpinnerButton";
import { MessageLevel } from "../messages/Message";
import { showMessage } from "../messages/MessageContainer";
import { Table, TableColumn } from "../table/Table";

type BulkDeleteMetadata = { key: string; value: string }[];

@customElement("ak-delete-objects-table")
export class DeleteObjectsTable<T> extends Table<T> {
    expandable = true;
    paginated = false;

    @property({ attribute: false })
    objects: T[] = [];

    @property({ attribute: false })
    metadata!: (item: T) => BulkDeleteMetadata;

    @property({ attribute: false })
    usedBy?: (item: T) => Promise<UsedBy[]>;

    @state()
    usedByData: Map<T, UsedBy[]> = new Map();

    static get styles(): CSSResult[] {
        return super.styles.concat(PFList);
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    async apiEndpoint(page: number): Promise<AKResponse<T>> {
        return Promise.resolve({
            pagination: {
                count: this.objects.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: this.objects.length,
            },
            results: this.objects,
        });
    }

    columns(): TableColumn[] {
        return this.metadata(this.objects[0]).map((element) => {
            return new TableColumn(element.key);
        });
    }

    row(item: T): TemplateResult[] {
        return this.metadata(item).map((element) => {
            return html`${element.value}`;
        });
    }

    renderToolbarContainer(): TemplateResult {
        return html``;
    }

    renderExpanded(item: T): TemplateResult {
        const handler = async () => {
            if (!this.usedByData.has(item) && this.usedBy) {
                this.usedByData.set(item, await this.usedBy(item));
            }
            return this.renderUsedBy(this.usedByData.get(item) || []);
        };
        return html`<td role="cell" colspan="2">
            <div class="pf-c-table__expandable-row-content">
                ${this.usedBy
                    ? until(handler(), html`<ak-spinner size=${PFSize.Large}></ak-spinner>`)
                    : html``}
            </div>
        </td>`;
    }

    renderUsedBy(usedBy: UsedBy[]): TemplateResult {
        if (usedBy.length < 1) {
            return html`<span>${t`Not used by any other object.`}</span>`;
        }
        return html`<ul class="pf-c-list">
            ${usedBy.map((ub) => {
                let consequence = "";
                switch (ub.action) {
                    case UsedByActionEnum.Cascade:
                        consequence = t`object will be DELETED`;
                        break;
                    case UsedByActionEnum.CascadeMany:
                        consequence = t`connection will be deleted`;
                        break;
                    case UsedByActionEnum.SetDefault:
                        consequence = t`reference will be reset to default value`;
                        break;
                    case UsedByActionEnum.SetNull:
                        consequence = t`reference will be set to an empty value`;
                        break;
                }
                return html`<li>${t`${ub.name} (${consequence})`}</li>`;
            })}
        </ul>`;
    }
}

@customElement("ak-forms-delete-bulk")
export class DeleteBulkForm extends ModalButton {
    @property({ attribute: false })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    objects: any[] = [];

    @property()
    objectLabel?: string;

    @property({ attribute: false })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    metadata: (item: any) => BulkDeleteMetadata = (item: any) => {
        const rec = item as Record<string, unknown>;
        const meta = [];
        if (Object.prototype.hasOwnProperty.call(rec, "name")) {
            meta.push({ key: t`Name`, value: rec.name as string });
        }
        if (Object.prototype.hasOwnProperty.call(rec, "pk")) {
            meta.push({ key: t`ID`, value: rec.pk as string });
        }
        return meta;
    };

    @property({ attribute: false })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    usedBy?: (item: any) => Promise<UsedBy[]>;

    @property({ attribute: false })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete!: (item: any) => Promise<any>;

    confirm(): Promise<void> {
        return Promise.all(
            this.objects.map((item) => {
                return this.delete(item);
            }),
        )
            .then(() => {
                this.onSuccess();
                this.open = false;
                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );
            })
            .catch((e) => {
                this.onError(e);
                throw e;
            });
    }

    onSuccess(): void {
        showMessage({
            message: t`Successfully deleted ${this.objects.length} ${this.objectLabel}`,
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
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${t`Delete ${this.objectLabel}`}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-c-page__main-section pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p class="pf-c-title">
                        ${t`Are you sure you want to delete ${this.objects.length} ${this.objectLabel}?`}
                    </p>
                    <slot name="notice"></slot>
                </form>
            </section>
            <section class="pf-c-modal-box__body pf-c-page__main-section pf-m-light">
                <ak-delete-objects-table
                    .objects=${this.objects}
                    .usedBy=${this.usedBy}
                    .metadata=${this.metadata}
                >
                </ak-delete-objects-table>
            </section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm();
                    }}
                    class="pf-m-danger"
                >
                    ${t`Delete`} </ak-spinner-button
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
