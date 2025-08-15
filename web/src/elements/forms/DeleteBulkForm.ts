import "#elements/buttons/SpinnerButton/index";

import { EVENT_REFRESH } from "#common/constants";
import { PFSize } from "#common/enums";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { ModalButton } from "#elements/buttons/ModalButton";
import { showMessage } from "#elements/messages/MessageContainer";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { UsedBy, UsedByActionEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

//#region Types

export interface DestroyableAPIObject {
    pk?: string;
    name?: string;
}

export interface BulkDeleteMetadata {
    key: string;
    value: string;
    className?: string;
}

export type BulkDeleteMetadataCallback<T extends DestroyableAPIObject = DestroyableAPIObject> = (
    item: T,
) => Iterable<BulkDeleteMetadata>;

const ConsquenceLabel = {
    [UsedByActionEnum.Cascade]: msg("Object will be DELETED"),
    [UsedByActionEnum.CascadeMany]: msg("Connection will be deleted"),
    [UsedByActionEnum.SetDefault]: msg("Reference will be reset to default value"),
    [UsedByActionEnum.SetNull]: msg("Reference will be set to an empty value"),
    [UsedByActionEnum.UnknownDefaultOpenApi]: msg("Unknown action"),
} as const satisfies Record<UsedByActionEnum, string>;

//#endregion

//#region Table

@customElement("ak-delete-objects-table")
export class DeleteObjectsTable<T extends DestroyableAPIObject> extends Table<T> {
    static styles: CSSResult[] = [
        ...super.styles,
        PFList,
        css`
            .pf-c-table__expandable-row-content {
                min-height: 1rem;
            }
        `,
    ];

    public override paginated = false;

    @property({ attribute: false })
    public objects: Iterable<T> = [];

    @property({ attribute: false })
    public metadata?: BulkDeleteMetadataCallback<T>;

    @property({ attribute: false })
    public usedBy?: (item: T) => Promise<UsedBy[]>;

    //#region Lifecycle

    @state()
    protected usedByCache: Map<T, UsedBy[]> = new Map();

    protected override async apiEndpoint(): Promise<PaginatedResponse<T>> {
        const results = Array.from(this.objects);

        return Promise.resolve({
            pagination: {
                count: results.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: results.length,
                next: 0,
                previous: 0,
            },
            results,
        });
    }

    #fetchRelations = async (item: T): Promise<UsedBy[]> => {
        let relations = this.usedByCache.get(item);

        if (!relations && this.usedBy) {
            relations = await this.usedBy(item);
            this.usedByCache.set(item, relations);
        }

        return relations || [];
    };

    public override connectedCallback(): void {
        super.connectedCallback();
        this.expandable = !!this.usedBy;
    }

    //#endregion

    //#region Render

    protected override columns(): TableColumn[] {
        const objects = Array.from(this.objects);

        return Array.from(this.metadata?.(objects[0]) || [], ({ key }) => {
            return new TableColumn(key);
        });
    }

    protected override row(item: T): TemplateResult[] {
        return Array.from(
            this.metadata?.(item) || [],
            ({ value, className = "" }) => html` <span class="${className}"> ${value} </span>`,
        );
    }

    protected override renderToolbarContainer(): SlottedTemplateResult {
        return nothing;
    }

    protected override renderExpanded(item: T): TemplateResult {
        return html`<td role="cell" colspan="2">
            <div class="pf-c-table__expandable-row-content">
                ${this.usedBy
                    ? until(
                          this.#fetchRelations(item).then(this.#renderConsequences),
                          html`<ak-spinner size=${PFSize.Large}></ak-spinner>`,
                      )
                    : nothing}
            </div>
        </td>`;
    }

    #renderConsequences = (usedBy: UsedBy[]): TemplateResult => {
        if (usedBy.length === 0) {
            return html`<span>${msg("Not used by any other object.")}</span>`;
        }

        return html`<ul class="pf-c-list">
            ${usedBy.map((ub) => {
                const consequence = ConsquenceLabel[ub.action];

                return html`<li>${msg(str`${ub.name} (${consequence})`)}</li>`;
            })}
        </ul>`;
    };

    //#endregion
}

//#endregion

//#region Form

@customElement("ak-forms-delete-bulk")
export class DeleteBulkForm<T extends DestroyableAPIObject> extends ModalButton {
    //#region Properties

    @property({ attribute: false })
    public objects: Iterable<T> = [];

    @property()
    public objectLabel?: string;

    @property()
    public actionLabel?: string;

    @property()
    public actionSubtext?: string;

    @property()
    public buttonLabel = msg("Delete");

    /**
     * Action shown in messages, for example `deleted` or `removed`
     */
    @property()
    public action = msg("deleted");

    @property({ attribute: false })
    public metadata?: BulkDeleteMetadataCallback<T> = (item: T) => {
        const meta: BulkDeleteMetadata[] = [];

        if (item.name) {
            meta.push({ key: msg("Name"), value: item.name });
        }
        if (item.pk) {
            meta.push({ key: msg("ID"), value: item.pk, className: "pf-m-monospace" });
        }

        return meta;
    };

    @property({ attribute: false })
    public usedBy?: (item: T) => Promise<UsedBy[]>;

    @property({ attribute: false })
    public delete!: (item: T) => Promise<unknown>;

    //#endregion

    #send = (): Promise<void> => {
        const objects = Array.from(this.objects, (item) => this.delete(item));

        return Promise.all(objects)
            .then(() => {
                showMessage({
                    message: msg(str`Successfully deleted ${objects.length} ${this.objectLabel}`),
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
                    message: msg(
                        str`Failed to delete ${objects.length} ${this.objectLabel}: ${detail}`,
                    ),
                    level: MessageLevel.error,
                });
            });
    };

    //#region Render

    protected override renderModalInner(): TemplateResult {
        const objects = Array.from(this.objects);

        return html`<header class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 id="modal-title" class="pf-c-title pf-m-2xl">
                        ${this.actionLabel || msg(str`Confirm ${this.objectLabel} Deletion`)}
                    </h1>
                </div>
            </header>
            <div class="pf-c-modal-box__body pf-m-light">
                <div class="pf-m-horizontal">
                    <p class="pf-c-title">
                        ${this.actionSubtext
                            ? this.actionSubtext
                            : msg(
                                  str`Are you sure you want to delete ${objects.length} ${this.objectLabel}?`,
                              )}
                    </p>
                    <slot name="notice"></slot>
                </div>
            </div>
            <div class="pf-c-modal-box__body pf-m-light">
                <ak-delete-objects-table
                    label=${msg(str`${this.objectLabel} to be deleted`)}
                    .objects=${this.objects}
                    .usedBy=${this.usedBy}
                    .metadata=${this.metadata}
                >
                </ak-delete-objects-table>
            </div>
            <footer aria-label=${msg("Actions")} class="pf-c-modal-box__footer">
                <ak-spinner-button .callAction=${this.#send} class="pf-m-danger">
                    ${this.buttonLabel} ${objects.length.toLocaleString()} ${this.objectLabel} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${() => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}

//#endregion

declare global {
    interface HTMLElementTagNameMap {
        "ak-delete-objects-table": DeleteObjectsTable<object>;
        "ak-forms-delete-bulk": DeleteBulkForm<object>;
    }
}
