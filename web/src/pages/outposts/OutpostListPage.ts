import { t } from "@lingui/macro";

import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { Outpost, OutpostTypeEnum, OutpostsApi } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { uiConfig } from "../../common/config";
import { PFSize } from "../../elements/Spinner";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import "./OutpostDeploymentModal";
import "./OutpostForm";
import "./OutpostHealth";
import "./OutpostHealthSimple";

export function TypeToLabel(type?: OutpostTypeEnum): string {
    if (!type) return "";
    switch (type) {
        case OutpostTypeEnum.Proxy:
            return t`Proxy`;
        case OutpostTypeEnum.Ldap:
            return t`LDAP`;
    }
}

@customElement("ak-outpost-list")
export class OutpostListPage extends TablePage<Outpost> {
    expandable = true;

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
    async apiEndpoint(page: number): Promise<AKResponse<Outpost>> {
        return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }
    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Type`, "type"),
            new TableColumn(t`Providers`),
            new TableColumn(t`Integration`, "service_connection__name"),
            new TableColumn(t`Health and Version`),
            new TableColumn(t`Actions`),
        ];
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    checkbox = true;

    @property()
    order = "name";

    row(item: Outpost): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
                ${item.config.authentik_host === ""
                    ? html`<i class="pf-icon pf-icon-warning-triangle"></i>
                          <small
                              >${t`Warning: authentik Domain is not configured, authentication will not work.`}</small
                          >`
                    : html`<i class="pf-icon pf-icon-ok"></i>
                          <small> ${t`Logging in via ${item.config.authentik_host}.`} </small>`}
            </div>`,
            html`${TypeToLabel(item.type)}`,
            html`<ul>
                ${item.providersObj?.map((p) => {
                    return html`<li>
                        <a href="#/core/providers/${p.pk}">${p.name}</a>
                    </li>`;
                })}
            </ul>`,
            html`${item.serviceConnectionObj?.name || t`No integration active`}`,
            html`<ak-outpost-health-simple
                outpostId=${ifDefined(item.pk)}
            ></ak-outpost-health-simple>`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Outpost`} </span>
                    <ak-outpost-form
                        slot="form"
                        .instancePk=${item.pk}
                        .embedded=${item.managed === "goauthentik.io/outposts/embedded"}
                    >
                    </ak-outpost-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                ${item.managed !== "goauthentik.io/outposts/embedded"
                    ? html`<ak-outpost-deployment-modal .outpost=${item} size=${PFSize.Medium}>
                          <button slot="trigger" class="pf-c-button pf-m-tertiary">
                              ${t`View Deployment Info`}
                          </button>
                      </ak-outpost-deployment-modal>`
                    : html``}`,
        ];
    }

    renderExpanded(item: Outpost): TemplateResult {
        return html`<td role="cell" colspan="5">
            <div class="pf-c-table__expandable-row-content">
                <h3>
                    ${t`Detailed health (one instance per column, data is cached so may be out of data)`}
                </h3>
                <dl class="pf-c-description-list pf-m-3-col-on-lg">
                    ${until(
                        new OutpostsApi(DEFAULT_CONFIG)
                            .outpostsInstancesHealthList({
                                uuid: item.pk,
                            })
                            .then((health) => {
                                return health.map((h) => {
                                    return html` <div class="pf-c-description-list__group">
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <ak-outpost-health
                                                    .outpostHealth=${h}
                                                ></ak-outpost-health>
                                            </div>
                                        </dd>
                                    </div>`;
                                });
                            }),
                    )}
                </dl>
            </div>
        </td>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Outpost(s)`}
            .objects=${this.selectedElements}
            .usedBy=${(item: Outpost) => {
                return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesUsedByList({
                    uuid: item.pk,
                });
            }}
            .delete=${(item: Outpost) => {
                return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesDestroy({
                    uuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Outpost`} </span>
                <ak-outpost-form slot="form"> </ak-outpost-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
        `;
    }
}
