import "@goauthentik/admin/enterprise/EnterpriseLicenseForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/Spinner";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/cards/AggregateCard";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { EnterpriseApi, License, LicenseForecast, LicenseSummary } from "@goauthentik/api";

@customElement("ak-enterprise-license-list")
export class EnterpriseLicenseListPage extends TablePage<License> {
    checkbox = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Licenses");
    }
    pageDescription(): string {
        return msg("Manage enterprise licenses");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-key";
    }

    @property()
    order = "name";

    @state()
    forecast?: LicenseForecast;

    @state()
    summary?: LicenseSummary;

    @state()
    installID?: string;

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFDescriptionList,
            PFGrid,
            PFBanner,
            PFFormControl,
            PFButton,
            PFCard,
            css`
                .pf-m-no-padding-bottom {
                    padding-bottom: 0;
                }
            `,
        );
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<License>> {
        this.forecast = await new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseForecastRetrieve();
        this.summary = await new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseSummaryRetrieve();
        this.installID = (
            await new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseGetInstallIdRetrieve()
        ).installId;
        return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Users")),
            new TableColumn(msg("Expiry date")),
            new TableColumn(msg("Actions")),
        ];
    }

    // TODO: Make this more generic, maybe automatically get the plural name
    // of the object to use in the renderEmpty
    renderEmpty(inner?: TemplateResult): TemplateResult {
        return super.renderEmpty(html`
            ${inner
                ? inner
                : html`<ak-empty-state
                      icon=${this.pageIcon()}
                      header="${msg("No licenses found.")}"
                  >
                      <div slot="body">
                          ${this.searchEnabled() ? this.renderEmptyClearSearch() : html``}
                      </div>
                      <div slot="primary">${this.renderObjectCreate()}</div>
                  </ak-empty-state>`}
        `);
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("License(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: License) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Expiry"), value: item.expiry?.toLocaleString() },
                ];
            }}
            .usedBy=${(item: License) => {
                return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseUsedByList({
                    licenseUuid: item.licenseUuid,
                });
            }}
            .delete=${(item: License) => {
                return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseDestroy({
                    licenseUuid: item.licenseUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderSectionBefore(): TemplateResult {
        return html`
            <div class="pf-c-banner pf-m-info">
                ${msg("Enterprise is in preview.")}
                <a href="mailto:hello@goauthentik.io">${msg("Send us feedback!")}</a>
            </div>
            <section class="pf-c-page__main-section pf-m-no-padding-bottom">
                <div
                    class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-3-col-on-lg pf-m-all-3-col-on-xl"
                >
                    <div class="pf-l-grid__item pf-c-card">
                        <div class="pf-c-card__title">${msg("Get a license")}</div>
                        <div class="pf-c-card__body">
                            ${this.installID
                                ? html` <a
                                      target="_blank"
                                      href=${`https://customers.goauthentik.io/from_authentik/purchase/?install_id=${encodeURIComponent(
                                          this.installID,
                                      )}&authentik_url=${encodeURI(window.location.origin)}`}
                                      class="pf-c-button pf-m-primary pf-m-block"
                                      >${msg("Go to Customer Portal")}</a
                                  >`
                                : html`<ak-spinner></ak-spinner>`}
                        </div>
                    </div>

                    <ak-aggregate-card
                        class="pf-l-grid__item"
                        icon="pf-icon pf-icon-user"
                        header=${msg("Forecast internal users")}
                        subtext=${msg(
                            str`Estimated user count one year from now based on ${this.forecast?.users} current internal users and ${this.forecast?.forecastedUsers} forecasted internal users.`,
                        )}
                    >
                        ~&nbsp;${(this.forecast?.users || 0) +
                        (this.forecast?.forecastedUsers || 0)}
                    </ak-aggregate-card>
                    <ak-aggregate-card
                        class="pf-l-grid__item"
                        icon="pf-icon pf-icon-user"
                        header=${msg("Forecast external users")}
                        subtext=${msg(
                            str`Estimated user count one year from now based on ${this.forecast?.externalUsers} current external users and ${this.forecast?.forecastedExternalUsers} forecasted external users.`,
                        )}
                    >
                        ~&nbsp;${(this.forecast?.externalUsers || 0) +
                        (this.forecast?.forecastedExternalUsers || 0)}
                    </ak-aggregate-card>
                    <ak-aggregate-card
                        class="pf-l-grid__item"
                        icon="pf-icon pf-icon-user"
                        header=${msg("Expiry")}
                        subtext=${msg("Cumulative license expiry")}
                    >
                        ${this.summary?.hasLicense
                            ? this.summary.latestValid.toLocaleString()
                            : "-"}
                    </ak-aggregate-card>
                </div>
            </section>
        `;
    }

    row(item: License): TemplateResult[] {
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
            html`<div>
                <small>0 / ${item.users}</small>
                <small>0 / ${item.externalUsers}</small>
            </div>`,
            html`<ak-label color=${color}> ${item.expiry?.toLocaleString()} </ak-label>`,
            html`<ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update License")} </span>
                <ak-enterprise-license-form slot="form" .instancePk=${item.licenseUuid}>
                </ak-enterprise-license-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Install")} </span>
                <span slot="header"> ${msg("Install License")} </span>
                <ak-enterprise-license-form slot="form"> </ak-enterprise-license-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Install")}</button>
            </ak-forms-modal>
        `;
    }
}
