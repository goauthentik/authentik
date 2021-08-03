import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { AKResponse } from "../../api/Client";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";

import "./OutpostHealth";
import "./OutpostForm";
import "./OutpostDeploymentModal";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/ModalForm";
import "../../elements/forms/DeleteForm";
import { PAGE_SIZE } from "../../constants";
import { Outpost, OutpostsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import { PFSize } from "../../elements/Spinner";

@customElement("ak-outpost-list")
export class OutpostListPage extends TablePage<Outpost> {
    pageTitle(): string {
        return t`Outposts`;
    }
    pageDescription(): string | undefined {
        return t`Outposts are deployments of authentik components to support different environments and protocols, like reverse proxies.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-zone";
    }
    searchEnabled(): boolean {
        return true;
    }
    apiEndpoint(page: number): Promise<AKResponse<Outpost>> {
        return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }
    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Providers`),
            new TableColumn(t`Integration`, "service_connection__name"),
            new TableColumn(t`Health and Version`),
            new TableColumn(""),
        ];
    }

    @property()
    order = "name";

    row(item: Outpost): TemplateResult[] {
        if (item.managed === "goauthentik.io/outposts/embedded") {
            return this.rowInbuilt(item);
        }
        return [
            html`${item.name}`,
            html`<ul>
                ${item.providersObj?.map((p) => {
                    return html`<li>
                        <a href="#/core/providers/${p.pk}">${p.name}</a>
                    </li>`;
                })}
            </ul>`,
            html`${item.serviceConnectionObj?.name || t`No integration active`}`,
            html`<ak-outpost-health outpostId=${ifDefined(item.pk)}></ak-outpost-health>`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Outpost`} </span>
                    <ak-outpost-form slot="form" .instancePk=${item.pk}> </ak-outpost-form>
                    <button slot="trigger" class="pf-c-button pf-m-secondary">${t`Edit`}</button>
                </ak-forms-modal>
                <ak-forms-delete
                    .obj=${item}
                    objectLabel=${t`Outpost`}
                    .usedBy=${() => {
                        return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesUsedByList({
                            uuid: item.pk,
                        });
                    }}
                    .delete=${() => {
                        return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesDestroy({
                            uuid: item.pk,
                        });
                    }}
                >
                    <button slot="trigger" class="pf-c-button pf-m-danger">${t`Delete`}</button>
                </ak-forms-delete>
                <ak-outpost-deployment-modal .outpost=${item} size=${PFSize.Medium}>
                    <button slot="trigger" class="pf-c-button pf-m-tertiary">
                        ${t`View Deployment Info`}
                    </button>
                </ak-outpost-deployment-modal>`,
        ];
    }

    rowInbuilt(item: Outpost): TemplateResult[] {
        return [
            html`${item.name}`,
            html`<ul>
                ${item.providersObj?.map((p) => {
                    return html`<li>
                        <a href="#/core/providers/${p.pk}">${p.name}</a>
                    </li>`;
                })}
            </ul>`,
            html`${item.serviceConnectionObj?.name || t`No integration active`}`,
            html`<ak-outpost-health
                .showVersion=${false}
                outpostId=${ifDefined(item.pk)}
            ></ak-outpost-health>`,
            html`<ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update Outpost`} </span>
                <ak-outpost-form slot="form" .instancePk=${item.pk}> </ak-outpost-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">${t`Edit`}</button>
            </ak-forms-modal>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Outpost`} </span>
                <ak-outpost-form slot="form"> </ak-outpost-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}
