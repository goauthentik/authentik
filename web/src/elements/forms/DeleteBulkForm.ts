import { t } from "@lingui/macro";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { EVENT_REFRESH } from "../../constants";
import { ModalButton } from "../buttons/ModalButton";
import { MessageLevel } from "../messages/Message";
import { showMessage } from "../messages/MessageContainer";
import "../buttons/SpinnerButton";
import { UsedBy, UsedByActionEnum } from "authentik-api";
import PFList from "@patternfly/patternfly/components/List/list.css";
import { until } from "lit-html/directives/until";
import { Table, TableColumn } from "../table/Table";
import { AKResponse } from "../../api/Client";
import { PFSize } from "../Spinner";

export interface AKObject<T extends string | number> {
    pk: T;
    slug?: string;
    name?: string;
    [key: string]: unknown;
}

@customElement("ak-delete-objects-table")
export class DeleteObjectsTable<ObjPkT extends string | number> extends Table<AKObject<ObjPkT>> {
    expandable = true;
    paginated = false;

    @property({ attribute: false })
    objects: AKObject<ObjPkT>[] = [];

    @property({ attribute: false })
    usedBy?: (item: AKObject<ObjPkT>) => Promise<UsedBy[]>;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFList);
    }

    apiEndpoint(page: number): Promise<AKResponse<AKObject<ObjPkT>>> {
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
        return [new TableColumn(t`Name`), new TableColumn(t`ID`)];
    }

    row(item: AKObject<ObjPkT>): TemplateResult[] {
        return [html`${item.name}`, html`${item.pk}`];
    }

    renderToolbarContainer(): TemplateResult {
        return html``;
    }

    renderExpanded(item: AKObject<ObjPkT>): TemplateResult {
        return html`${this.usedBy
            ? until(
                  this.usedBy(item).then((usedBy) => {
                      return this.renderUsedBy(item, usedBy);
                  }),
                  html`<ak-spinner size=${PFSize.XLarge}></ak-spinner>`,
              )
            : html``}`;
    }

    renderUsedBy(item: AKObject<ObjPkT>, usedBy: UsedBy[]): TemplateResult {
        if (usedBy.length < 1) {
            return html`<td role="cell" colspan="2">
                <div class="pf-c-table__expandable-row-content">
                    <span>${t`Not used by any other object.`}</span>
                </div>
            </td>`;
        }
        return html`<td role="cell" colspan="2">
            <div class="pf-c-table__expandable-row-content">
                <p>${t`The following objects use ${item.name}:`}</p>
                <ul class="pf-c-list">
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
                </ul>
            </div>
        </td> `;
    }
}

@customElement("ak-forms-delete-bulk")
export class DeleteBulkForm<ObjPkT extends string | number> extends ModalButton {
    @property({ attribute: false })
    objects: AKObject<ObjPkT>[] = [];

    @property()
    objectLabel?: string;

    @property({ attribute: false })
    usedBy?: (itemPk: AKObject<ObjPkT>) => Promise<UsedBy[]>;

    @property({ attribute: false })
    delete!: (itemPk: AKObject<ObjPkT>) => Promise<unknown>;

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
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${t`Delete ${this.objectLabel}`}</h1>
                </div>
            </section>
            <section class="pf-c-page__main-section pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p>
                        ${t`Are you sure you want to delete ${this.objects.length} ${this.objectLabel}?`}
                    </p>
                </form>
            </section>
            <section class="pf-c-page__main-section">
                <ak-delete-objects-table .objects=${this.objects} .usedBy=${this.usedBy}>
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
