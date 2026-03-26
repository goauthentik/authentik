import "#admin/outposts/OutpostForm";
import "#admin/outposts/OutpostHealthSimple";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { OutpostForm } from "#admin/outposts/OutpostForm";
import { embeddedOutpostManaged, outpostTypeToLabel } from "#admin/outposts/utils";

import { Outpost, OutpostHealth, OutpostsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-outpost-list")
export class OutpostListPage extends TablePage<Outpost> {
    protected override searchEnabled = true;

    public override searchPlaceholder = msg("Search outposts...");
    public override pageTitle = msg("Outposts");
    public override pageDescription = msg(
        "Outposts are deployments of authentik components to support different environments and protocols, like reverse proxies.",
    );

    public override pageIcon = "pf-icon pf-icon-zone";

    protected async apiEndpoint(): Promise<PaginatedResponse<Outpost>> {
        const outposts = await new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesList(
            await this.defaultEndpointConfig(),
        );
        await Promise.all(
            outposts.results.map((outpost) => {
                return new OutpostsApi(DEFAULT_CONFIG)
                    .outpostsInstancesHealthList({
                        uuid: outpost.pk,
                    })
                    .then((health) => {
                        this.health[outpost.pk] = health;
                    });
            }),
        );
        return outposts;
    }

    @state()
    protected health: Record<string, OutpostHealth[]> = {};

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type"), "type"],
        [msg("Providers")],
        [msg("Integration"), "service_connection__name"],
        [msg("Health and Version")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    public override checkbox = true;
    public override clearOnRefresh = true;

    @property({ type: String })
    public order = "name";

    protected openEditModal = (event: Event) => {
        const button = event.currentTarget as HTMLButtonElement;
        const instancePk = button.dataset.instancePk!;
        const managed = button.dataset.managed === "true";

        const form = new OutpostForm();

        form.instancePk = instancePk;
        form.embedded = managed;

        return form.showModal();
    };

    protected renderItemProviders(item: Outpost) {
        if (item.providers.length < 1) {
            return html`-`;
        }
        return html`<ul>
            ${item.providersObj?.map((p) => {
                return html`<li>
                    <a href="#/core/providers/${p.pk}">${p.name}</a>
                </li>`;
            })}
        </ul>`;
    }

    protected row(item: Outpost): SlottedTemplateResult[] {
        return [
            html`<a href="#/outpost/outposts/${item.pk}"
                ><div>${item.name}</div>
                ${(item.config.authentik_host ?? "") === ""
                    ? html`<ak-label color=${PFColor.Orange} compact>
                          ${msg(
                              "Warning: authentik Domain is not configured, authentication will not work.",
                          )}
                      </ak-label>`
                    : html`<ak-label color=${PFColor.Green} compact>
                          ${msg(str`Logging in via ${item.config.authentik_host}.`)}
                      </ak-label>`}</a
            >`,
            html`${outpostTypeToLabel(item.type)}`,
            this.renderItemProviders(item),
            html`${item.serviceConnectionObj?.name || msg("No integration active")}`,
            html`<ak-outpost-health-simple
                outpostId=${ifDefined(item.pk)}
            ></ak-outpost-health-simple>`,
            html`<button
                class="pf-c-button pf-m-plain"
                aria-label=${msg(str`Edit ${item.name}`)}
                data-instance-pk=${item.pk}
                data-managed=${item.managed === embeddedOutpostManaged}
                @click=${this.openEditModal}
            >
                <pf-tooltip position="top" content=${msg("Edit")}>
                    <i class="fas fa-edit" aria-hidden="true"></i>
                </pf-tooltip>
            </button>`,
        ];
    }

    protected override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Outpost(s)")}
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
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override renderObjectCreate(): TemplateResult {
        return html`<button ${OutpostForm.asModalInvoker()} class="pf-c-button pf-m-primary">
            ${msg("New Outpost")}
        </button>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-outpost-list": OutpostListPage;
    }
}
