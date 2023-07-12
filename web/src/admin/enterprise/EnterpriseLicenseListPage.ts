import "@goauthentik/admin/enterprise/EnterpriseLicenseForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/cards/AggregateCard";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { EnterpriseApi, License, LicenseForecast } from "@goauthentik/api";

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
        // TODO: add copy text
        return msg("TODO Copy");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-key";
    }

    @property()
    order = "name";

    @state()
    forecast?: LicenseForecast;

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFDescriptionList,
            PFGrid,
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
            <section class="pf-c-page__main-section pf-m-no-padding-bottom">
                <div
                    class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-3-col-on-lg pf-m-all-3-col-on-xl"
                >
                    <div class="pf-l-grid__item pf-c-card">
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-user"
                            header=${msg("Forecasted default users")}
                            subtext=${msg("TODO Copy")}
                        >
                            ${this.forecast?.users}
                        </ak-aggregate-card>
                    </div>
                    <div class="pf-l-grid__item pf-c-card">
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-user"
                            header=${msg("Forecasted external users")}
                            subtext=${msg("TODO Copy")}
                        >
                            ${this.forecast?.externalUsers}
                        </ak-aggregate-card>
                    </div>
                    <div class="pf-l-grid__item pf-c-card">
                        <div class="pf-c-card__body">item 3</div>
                    </div>
                    <div class="pf-l-grid__item pf-c-card">
                        <div class="pf-c-card__body"></div>
                    </div>
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
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create License")} </span>
                <ak-enterprise-license-form slot="form"> </ak-enterprise-license-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}
