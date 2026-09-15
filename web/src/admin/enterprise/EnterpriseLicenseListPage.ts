import "#admin/enterprise/EnterpriseLicenseForm";
import "#admin/enterprise/EnterpriseStatusCard";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/Spinner";
import "#elements/buttons/SpinnerButton/index";
import "#elements/cards/AggregateCard";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";
import { docLink } from "#common/global";

import { IconCopyButton } from "#elements/buttons/IconCopyButton";
import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { EnterpriseLicenseForm } from "#admin/enterprise/EnterpriseLicenseForm";

import {
    EnterpriseApi,
    License,
    LicenseSummary,
    LicenseSummaryStatusEnum,
    LicenseUserCounts,
    ModelEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-enterprise-license-list")
export class EnterpriseLicenseListPage extends TablePage<License> {
    public static styles: CSSResult[] = [
        ...super.styles,
        PFGrid,
        PFBanner,
        PFFormControl,
        PFButton,
        PFCard,
        css`
            .pf-m-no-padding-bottom {
                padding-bottom: 0;
            }
            .install-id {
                align-items: center;
                display: flex;
                gap: var(--pf-global--spacer--xs);
            }
            .install-id-value {
                min-width: 0;
                overflow-wrap: anywhere;
            }
            .user-growth-card::part(card-body) {
                padding-top: var(--pf-global--spacer--xs);
            }
            .user-growth__title {
                color: var(--pf-global--Color--200);
                font-size: var(--pf-global--FontSize--md);
                margin-bottom: var(--pf-global--spacer--xs);
            }
            .user-growth {
                margin: 0;
            }
            .user-growth__row {
                align-items: center;
                display: flex;
                justify-content: space-between;
                padding-block: var(--pf-global--spacer--xs);
            }
            .user-growth__row + .user-growth__row {
                border-top: var(--pf-global--BorderWidth--sm) solid
                    var(--pf-global--BorderColor--100);
            }
            .user-growth__period,
            .user-growth__count {
                margin: 0;
            }
            .user-growth__count {
                font-size: var(--pf-global--FontSize--lg);
                font-variant-numeric: tabular-nums;
                font-weight: var(--pf-global--FontWeight--bold);
                margin-left: var(--pf-global--spacer--md);
            }
            .user-total {
                align-items: baseline;
                border-bottom: var(--pf-global--BorderWidth--sm) solid
                    var(--pf-global--BorderColor--100);
                display: flex;
                gap: var(--pf-global--spacer--sm);
                margin-bottom: var(--pf-global--spacer--sm);
                padding-bottom: var(--pf-global--spacer--sm);
            }
            .user-total__count {
                font-size: var(--pf-global--FontSize--2xl);
                font-variant-numeric: tabular-nums;
                font-weight: var(--pf-global--FontWeight--bold);
                line-height: 1;
            }
            .user-total__label {
                color: var(--pf-global--Color--200);
                font-size: var(--pf-global--FontSize--sm);
            }
        `,
    ];

    public override checkbox = true;
    public override clearOnRefresh = true;

    protected override searchEnabled = true;
    public override pageTitle = msg("Licenses");
    public override pageDescription = msg("Manage enterprise licenses");
    public override pageIcon = "pf-icon pf-icon-key";
    public override searchPlaceholder = msg("Search for a license by name...");
    public override order = "name";

    @state()
    protected userCounts?: LicenseUserCounts;

    @state()
    protected summary?: LicenseSummary;

    @state()
    protected installID?: string;

    async apiEndpoint(): Promise<PaginatedResponse<License>> {
        this.userCounts = await aki(EnterpriseApi).enterpriseLicenseUserCountsRetrieve({
            countSteps: ["days=30", "days=90", "days=365"],
        });
        this.summary = await aki(EnterpriseApi).enterpriseLicenseSummaryRetrieve({
            cached: false,
        });
        this.installID = (await aki(EnterpriseApi).enterpriseLicenseInstallIdRetrieve()).installId;
        return aki(EnterpriseApi).enterpriseLicenseList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Users")],
        [msg("Expiry date")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    // TODO: Make this more generic, maybe automatically get the plural name
    // of the object to use in the renderEmpty
    protected override renderEmpty(inner?: SlottedTemplateResult): SlottedTemplateResult {
        return super.renderEmpty(html`
            ${inner
                ? inner
                : html`<ak-empty-state icon=${this.pageIcon}
                      ><span>${msg("No licenses found.")}</span>
                      <div slot="body">
                          ${this.searchEnabled ? this.renderEmptyClearSearch() : nothing}
                      </div>
                      <div slot="primary">${this.renderObjectCreate()}</div>
                  </ak-empty-state>`}
        `);
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("License(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: License) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Expiry"), value: item.expiry?.toLocaleString() },
                ];
            }}
            .usedBy=${(item: License) => {
                return aki(EnterpriseApi).enterpriseLicenseUsedByList({
                    licenseUuid: item.licenseUuid,
                });
            }}
            .delete=${(item: License) => {
                return aki(EnterpriseApi).enterpriseLicenseDestroy({
                    licenseUuid: item.licenseUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override renderSectionBefore(): SlottedTemplateResult {
        const {
            activeInternalUsers = 0,
            activeExternalUsers = 0,
            ranges = [],
        } = this.userCounts || {};
        const countsByInterval = new Map(ranges.map((range) => [range.interval, range]));
        const last30Days = countsByInterval.get("days=30");
        const last90Days = countsByInterval.get("days=90");
        const last365Days = countsByInterval.get("days=365");

        const renderUserGrowth = (
            totalUsers: number,
            totalLabel: string,
            last30Days: number,
            last90Days: number,
            last365Days: number,
        ) => {
            const periods = [
                {
                    label: msg("30 days", {
                        id: "enterprise.licensing.users.added-within.30-days.label",
                    }),
                    value: last30Days,
                },
                {
                    label: msg("90 days", {
                        id: "enterprise.licensing.users.added-within.90-days.label",
                    }),
                    value: last90Days,
                },
                {
                    label: msg("365 days", {
                        id: "enterprise.licensing.users.added-within.365-days.label",
                    }),
                    value: last365Days,
                },
            ];

            return html`<div class="user-total">
                    <span class="user-total__count">${totalUsers}</span>
                    <span class="user-total__label">${totalLabel}</span>
                </div>
                <div class="user-growth__title">
                    ${msg("Added within last", {
                        id: "enterprise.licensing.users.added-within-last.title",
                    })}
                </div>
                <dl class="user-growth">
                    ${periods.map(
                        (period) =>
                            html`<div class="user-growth__row">
                                <dt class="user-growth__period">${period.label}</dt>
                                <dd class="user-growth__count">${period.value}</dd>
                            </div>`,
                    )}
                </dl>`;
        };

        return html`
            <section class="pf-c-page__main-section pf-m-no-padding-bottom">
                <div
                    class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-3-col-on-lg pf-m-all-3-col-on-xl"
                >
                    ${this.renderGetLicenseCard()}
                    <ak-aggregate-card
                        class="pf-l-grid__item user-growth-card"
                        icon="pf-icon pf-icon-user"
                        label=${msg("Internal users", {
                            id: "enterprise.licensing.internal-users.label",
                        })}
                    >
                        ${renderUserGrowth(
                            activeInternalUsers,
                            msg("Total active internal users", {
                                id: "enterprise.licensing.internal-users.total-active.label",
                            }),
                            last30Days?.internalUsersAdded ?? 0,
                            last90Days?.internalUsersAdded ?? 0,
                            last365Days?.internalUsersAdded ?? 0,
                        )}
                    </ak-aggregate-card>
                    <ak-aggregate-card
                        class="pf-l-grid__item user-growth-card"
                        icon="pf-icon pf-icon-user"
                        label=${msg("External users", {
                            id: "enterprise.licensing.external-users.label",
                        })}
                    >
                        ${renderUserGrowth(
                            activeExternalUsers,
                            msg("Total active external users", {
                                id: "enterprise.licensing.external-users.total-active.label",
                            }),
                            last30Days?.externalUsersAdded ?? 0,
                            last90Days?.externalUsersAdded ?? 0,
                            last365Days?.externalUsersAdded ?? 0,
                        )}
                    </ak-aggregate-card>
                    <ak-aggregate-card
                        role="status"
                        class="pf-l-grid__item"
                        icon="pf-icon pf-icon-user"
                        label=${msg("Expiry")}
                        subtext=${msg("Cumulative license expiry")}
                        >${this.summary &&
                        this.summary?.status !== LicenseSummaryStatusEnum.Unlicensed
                            ? Timestamp(this.summary.latestValid)
                            : html`<span aria-label=${msg("No expiry")}
                                  >-</span
                              >`}</ak-aggregate-card
                    >
                </div>
            </section>
            <section class="pf-c-page__main-section pf-m-no-padding-bottom">
                <ak-enterprise-status-card
                    .summary=${this.summary}
                    .userCounts=${this.userCounts}
                ></ak-enterprise-status-card>
            </section>
        `;
    }

    row(item: License): SlottedTemplateResult[] {
        let color = PFColor.Green;
        if (item.expiry) {
            const now = new Date();
            const inAMonth = new Date();
            inAMonth.setDate(inAMonth.getDate() + 30);
            if (item.expiry <= inAMonth) {
                color = PFColor.Orange;
            }
            if (item.expiry <= now) {
                color = PFColor.Red;
            }
        }
        return [
            html`<div>${item.name}</div>`,
            html`<div>${msg(str`Internal: ${item.internalUsers}`)}</div>
                <div>${msg(str`External: ${item.externalUsers}`)}</div>`,
            html`<ak-label color=${color}> ${item.expiry?.toLocaleString()} </ak-label>`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(EnterpriseLicenseForm, item.licenseUuid, item.name)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikEnterpriseLicense}
                    objectPk=${item.licenseUuid}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected renderGetLicenseCard() {
        const renderSpinner = () =>
            html` <div class="pf-c-card__body">
                <ak-spinner></ak-spinner>
            </div>`;

        const installURL = (installID: string) =>
            [
                "https://customers.goauthentik.io/from_authentik/purchase/?install_id=",
                encodeURIComponent(installID),
                "&authentik_url=",
                encodeURI(window.location.origin),
            ].join("");

        const renderCard = (installID: string) => html`
            <div class="pf-c-card__title">${msg("Your Install ID")}</div>
            <div class="pf-c-card__body install-id pf-m-monospace">
                <span class="install-id-value">${installID}</span>
                ${IconCopyButton({
                    source: installID,
                    buttonLabel: msg("Copy Install ID", {
                        id: "enterprise.licensing.install-id.copy-button.label",
                    }),
                    entityLabel: msg("Install ID", {
                        id: "enterprise.licensing.install-id.label",
                    }),
                })}
            </div>
            <div class="pf-c-card__body">
                <a
                    target="_blank"
                    href="${installURL(installID)}"
                    class="pf-c-button pf-m-primary pf-m-block"
                    >${msg("Go to Customer Portal")}</a
                >
            </div>
            <div class="pf-c-card__body">
                <a target="_blank" href=${docLink("/enterprise/get-started")}
                    >${msg("Learn more")}</a
                >
            </div>
        `;

        return html`<div class="pf-l-grid__item pf-c-card">
            ${this.installID ? renderCard(this.installID) : renderSpinner()}
        </div> `;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(EnterpriseLicenseForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enterprise-license-list": EnterpriseLicenseListPage;
    }
}
