import "#elements/buttons/SpinnerButton/index";

import { EVENT_REFRESH } from "#common/constants";
import { PFSize } from "#common/enums";
import { MessageLevel } from "#common/messages";

import { ModalButton } from "#elements/buttons/ModalButton";
import { showMessage } from "#elements/messages/MessageContainer";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { UsedBy, UsedByActionEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

type BulkDeleteMetadata = { key: string; value: string }[];

@customElement("ak-delete-objects-table")
export class DeleteObjectsTable<T extends object> extends Table<T> {
    static styles: CSSResult[] = [...super.styles, PFList];

    public override paginated = false;

    @property({ attribute: false })
    public objects: T[] = [];

    @property({ attribute: false })
    public metadata: (item: T) => BulkDeleteMetadata = (item: T) => {
        const metadata: BulkDeleteMetadata = [];
        if ("name" in item) {
            metadata.push({ key: msg("Name"), value: item.name as string });
        }
        return metadata;
    };

    @property({ attribute: false })
    public usedBy?: (item: T) => Promise<UsedBy[]>;

    @state()
    protected usedByData: Map<T, UsedBy[]> = new Map();

    protected async apiEndpoint(): Promise<PaginatedResponse<T>> {
        return Promise.resolve({
            pagination: {
                count: this.objects.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: this.objects.length,
                next: 0,
                previous: 0,
            },
            results: this.objects,
        });
    }

    protected override rowLabel(item: T): string | null {
        const name = "name" in item && typeof item.name === "string" ? item.name.trim() : null;
        return name || null;
    }

    @state()
    protected get columns(): TableColumn[] {
        return this.metadata(this.objects[0]).map((element) => [element.key]);
    }

    protected row(item: T): SlottedTemplateResult[] {
        return this.metadata(item).map((element) => {
            return html`${element.value}`;
        });
    }

    protected override renderToolbarContainer(): SlottedTemplateResult {
        return nothing;
    }

    protected override firstUpdated(changedProperties: PropertyValues<this>): void {
        this.expandable = !!this.usedBy;
        super.firstUpdated(changedProperties);
    }

    protected override renderExpanded(item: T): TemplateResult {
        const handler = async () => {
            if (!this.usedByData.has(item) && this.usedBy) {
                this.usedByData.set(item, await this.usedBy(item));
            }
            return this.renderUsedBy(this.usedByData.get(item) || []);
        };
        return html`${this.usedBy
            ? until(handler(), html`<ak-spinner size=${PFSize.Large}></ak-spinner>`)
            : nothing}`;
    }

    protected renderUsedBy(usedBy: UsedBy[]): TemplateResult {
        if (usedBy.length < 1) {
            return html`<span>${msg("Not used by any other object.")}</span>`;
        }
        return html`<ul class="pf-c-list">
            ${usedBy.map((ub) => {
                let consequence = "";
                switch (ub.action) {
                    case UsedByActionEnum.Cascade:
                        consequence = msg("object will be DELETED");
                        break;
                    case UsedByActionEnum.CascadeMany:
                        consequence = msg("connection will be deleted");
                        break;
                    case UsedByActionEnum.SetDefault:
                        consequence = msg("reference will be reset to default value");
                        break;
                    case UsedByActionEnum.SetNull:
                        consequence = msg("reference will be set to an empty value");
                        break;
                    case UsedByActionEnum.LeftDangling:
                        consequence = msg("reference will be left dangling");
                        break;
                }
                return html`<li>${msg(str`${ub.name} (${consequence})`)}</li>`;
            })}
        </ul>`;
    }
}

@customElement("ak-forms-delete-bulk")
export class DeleteBulkForm<T> extends ModalButton {
    @property({ attribute: false })
    public objects: T[] = [];

    @property({ type: String, attribute: "object-label" })
    public objectLabel: string | null = null;

    @property({ type: String, attribute: "action-label" })
    public actionLabel: string | null = null;

    @property({ type: String, attribute: "action-subtext" })
    public actionSubtext: string | null = null;

    @property({ type: String, attribute: "button-label" })
    public buttonLabel = msg("Delete");

    /**
     * Action shown in messages, for example `deleted` or `removed`
     */
    @property()
    action = msg("deleted");

    @property({ attribute: false })
    metadata: (item: T) => BulkDeleteMetadata = (item: T) => {
        const rec = item as Record<string, unknown>;
        const meta = [];
        if (Object.prototype.hasOwnProperty.call(rec, "name")) {
            meta.push({ key: msg("Name"), value: rec.name as string });
        }
        if (Object.prototype.hasOwnProperty.call(rec, "pk")) {
            meta.push({ key: msg("ID"), value: rec.pk as string });
        }
        return meta;
    };

    @property({ attribute: false })
    usedBy?: (item: T) => Promise<UsedBy[]>;

    @property({ attribute: false })
    delete!: (item: T) => Promise<unknown>;

    async confirm(): Promise<void> {
        try {
            await Promise.all(
                this.objects.map((item) => {
                    return this.delete(item);
                }),
            );
            this.onSuccess();
            this.dispatchEvent(
                new CustomEvent(EVENT_REFRESH, {
                    bubbles: true,
                    composed: true,
                }),
            );
            this.open = false;
        } catch (e) {
            this.onError(e as Error);
            throw e;
        }
    }

    onSuccess(): void {
        showMessage({
            message: msg(str`Successfully deleted ${this.objects.length} ${this.objectLabel}`),
            level: MessageLevel.success,
        });
    }

    onError(e: Error): void {
        showMessage({
            message: msg(str`Failed to delete ${this.objectLabel}: ${e.toString()}`),
            level: MessageLevel.error,
        });
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">
                        ${this.actionLabel
                            ? this.actionLabel
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
                    ${this.buttonLabel} </ak-spinner-button
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
        "ak-delete-objects-table": DeleteObjectsTable<object>;
        "ak-forms-delete-bulk": DeleteBulkForm<object>;
    }
}
