import "#elements/buttons/SpinnerButton/index";

import { EVENT_REFRESH } from "#common/constants";
import { PFSize } from "#common/enums";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { AKModal } from "#elements/modals/ak-modal";
import { renderModal } from "#elements/modals/utils";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import { UsedBy, UsedByActionEnum } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

type BulkDeleteMetadata = { key: string; value: string }[];

//#region Delete Objects Table

@customElement("ak-delete-objects-table")
export class DeleteObjectsTable<T extends object> extends Table<T> {
    paginated = false;

    @property({ attribute: false })
    objects: T[] = [];

    @property({ attribute: false })
    metadata!: (item: T) => BulkDeleteMetadata;

    @property({ attribute: false })
    usedBy?: (item: T) => Promise<UsedBy[]>;

    @state()
    usedByData: Map<T, UsedBy[]> = new Map();

    static styles: CSSResult[] = [...super.styles, PFList];

    async apiEndpoint(): Promise<PaginatedResponse<T>> {
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

    row(item: T): SlottedTemplateResult[] {
        return this.metadata(item).map((element) => {
            return html`${element.value}`;
        });
    }

    renderToolbarContainer(): SlottedTemplateResult {
        return nothing;
    }

    firstUpdated(): void {
        this.expandable = this.usedBy !== undefined;
        super.firstUpdated();
    }

    renderExpanded(item: T): TemplateResult {
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

    renderUsedBy(usedBy: UsedBy[]): TemplateResult {
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

//#endregion

//#region Delete Bulk Form

@customElement("ak-forms-delete-bulk")
export class DeleteBulkForm<T> extends AKModal {
    public get headline() {
        return this.actionLabel ? this.actionLabel : msg(str`Delete ${this.objectLabel}`);
    }

    //#region Properties

    @property({ attribute: false })
    public objects: Iterable<T> = [];

    @property({ type: String, attribute: "object-label" })
    public objectLabel?: string;

    @property({ type: String, attribute: "action-label" })
    public actionLabel?: string;

    @property({ type: String, attribute: "action-subtext" })
    public actionSubtext?: string;

    @property({ type: String, attribute: "button-label" })
    public buttonLabel = msg("Delete");

    /**
     * Action shown in messages, for example `deleted` or `removed`
     */
    @property({ type: String })
    public action = msg("deleted");

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
    public usedBy?: (item: T) => Promise<UsedBy[]>;

    @property({ attribute: false })
    public delete!: (item: T) => Promise<unknown>;

    //#endregion

    protected confirm = async (): Promise<void> => {
        const deletedItems = Array.from(this.objects, (item) => this.delete(item));

        return Promise.all(deletedItems)
            .then(() => {
                showMessage({
                    message: msg(
                        str`Successfully deleted ${deletedItems.length} ${this.objectLabel}`,
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
            .catch(async (error) => {
                const parsedError = await parseAPIResponseError(error);

                const detail = pluckErrorDetail(parsedError);

                showMessage({
                    message: msg(str`Failed to delete ${this.objectLabel}: ${detail}`),
                    level: MessageLevel.error,
                });
            });
    };

    protected override render(): TemplateResult {
        const objectCount = Array.from(this.objects).length;

        return html`<div class="ak-modal__body">
                <form class="pf-c-form pf-m-horizontal">
                    <p class="pf-c-title">
                        ${this.actionSubtext ||
                        msg(
                            str`Are you sure you want to delete ${objectCount} ${this.objectLabel}?`,
                        )}
                    </p>
                    <slot name="notice"></slot>
                </form>
            </div>
            <div class="ak-modal__body">
                <ak-delete-objects-table
                    .objects=${this.objects}
                    .usedBy=${this.usedBy}
                    .metadata=${this.metadata}
                >
                </ak-delete-objects-table>
            </div>
            <fieldset class="ak-modal__footer">
                <legend class="sr-only">${msg("Form actions")}</legend>

                <ak-spinner-button .callAction=${this.confirm} class="pf-m-danger">
                    ${this.buttonLabel}
                </ak-spinner-button>
                <button
                    type="button"
                    class="pf-c-button pf-m-secondary"
                    @click=${this.closeListener}
                >
                    ${msg("Cancel")}
                </button>
            </fieldset>`;
    }
}

//#endregion

/**
 * Props for DeleteBulkForm component.
 */
export type DeleteBulkFormProps<T = unknown> = LitPropertyRecord<DeleteBulkForm<T>>;

/**
 * Render a DeleteBulkForm modal.
 *
 * @see {@linkcode renderDeleteBulkFormModal} for rendering the modal directly.
 *
 * @param props Properties to pass to the DeleteBulkForm component.
 * @returns A TemplateResult rendering the DeleteBulkForm component.
 */
export function renderDeleteBulkForm<T = unknown>(props: DeleteBulkFormProps<T>): TemplateResult {
    return html`<ak-forms-delete-bulk ${spread(props)}></ak-forms-delete-bulk>`;
}

/**
 * Render and display a DeleteBulkForm modal.
 *
 * @param props Properties to pass to the DeleteBulkForm component.
 * @returns A promise that resolves when the modal is closed.
 */
export function renderDeleteBulkFormModal<T = unknown>(
    props: DeleteBulkFormProps<T>,
): Promise<void> {
    return renderModal(renderDeleteBulkForm<T>(props));
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-delete-objects-table": DeleteObjectsTable<object>;
        "ak-forms-delete-bulk": DeleteBulkForm<object>;
    }
}
