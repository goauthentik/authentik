import "#admin/flows/FlowForm";
import "#admin/blueprints/BlueprintImportForm";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/ConfirmationForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AndNext, DEFAULT_CONFIG } from "#common/api/config";
import { docLink } from "#common/global";
import { groupBy } from "#common/utils";

import { IconEditButton, modalInvoker, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { FlowForm } from "#admin/flows/FlowForm";
import { DesignationToLabel } from "#admin/flows/utils";

import { Flow, FlowsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-flow-list")
export class FlowListPage extends TablePage<Flow> {
    static styles = [...super.styles, PFBanner];

    protected override searchEnabled = true;
    public override searchPlaceholder = msg("Search for a flow by name or identifier...");

    public override pageTitle = msg("Flows");
    public override pageDescription = msg(
        "Flows describe a chain of Stages to authenticate, enroll or recover a user. Stages are chosen based on policies applied to them.",
    );
    public override pageIcon = "pf-icon pf-icon-process-automation";

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "slug";

    async apiEndpoint(): Promise<PaginatedResponse<Flow>> {
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(await this.defaultEndpointConfig());
    }

    groupBy(items: Flow[]): [string, Flow[]][] {
        return groupBy(items, (flow) => {
            return DesignationToLabel(flow.designation);
        });
    }

    protected columns: TableColumn[] = [
        [msg("Identifier"), "slug"],
        [msg("Name"), "name"],
        [msg("Stages")],
        [msg("Policies")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Flow(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Flow) => {
                return new FlowsApi(DEFAULT_CONFIG).flowsInstancesUsedByList({
                    slug: item.slug,
                });
            }}
            .delete=${(item: Flow) => {
                return new FlowsApi(DEFAULT_CONFIG).flowsInstancesDestroy({
                    slug: item.slug,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Flow): SlottedTemplateResult[] {
        return [
            html`<a href="#/flow/flows/${item.slug}" class="pf-m-block">
                    <code>${item.slug}</code>
                </a>
                <small>${item.title}</small>`,
            item.name,
            Array.from(item.stages || []).length,
            Array.from(item.policies || []).length,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(FlowForm, item.slug, item.name)}
                <button
                    aria-label=${msg(str`Execute "${item.name}"`)}
                    class="pf-c-button pf-m-plain"
                    @click=${() => {
                        const finalURL = `${window.location.origin}/if/flow/${item.slug}/${AndNext(
                            `${window.location.pathname}#${window.location.hash}`,
                        )}`;
                        window.open(finalURL, "_blank");
                    }}
                >
                    <pf-tooltip position="top" content=${msg("Execute")}>
                        <i class="fas fa-play" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
                <a
                    class="pf-c-button pf-m-plain"
                    href=${item.exportUrl}
                    aria-label=${msg(str`Export "${item.name}"`)}
                >
                    <pf-tooltip position="top" content=${msg("Export")}>
                        <i class="fas fa-download" aria-hidden="true"></i>
                    </pf-tooltip>
                </a>
            </div>`,
        ];
    }

    protected renderObjectCreate(): SlottedTemplateResult {
        return [
            ModalInvokerButton(FlowForm),
            html`<button
                class="pf-c-button pf-m-primary"
                type="button"
                ${modalInvoker(() => {
                    return html`<ak-blueprint-import-form>
                        <a
                            target="_blank"
                            rel="noopener noreferrer"
                            href=${docLink("/add-secure-apps/flows-stages/flow/examples/flows/")}
                            slot="read-more-link"
                            >${msg("Flow Examples")}</a
                        >
                        <span slot="banner-warning">
                            ${msg(
                                "Warning: Flow imports are blueprint files, which may contain objects other than flows (such as users, policies, etc).",
                            )}<br />${msg(
                                "You should only import files from trusted sources and review blueprints before importing them.",
                            )}
                        </span>
                    </ak-blueprint-import-form>`;
                })}
            >
                ${msg("Import")}
            </button>`,
        ];
    }

    protected renderToolbar(): SlottedTemplateResult {
        return html`
            ${super.renderToolbar()}
            <ak-forms-confirm
                successMessage=${msg("Successfully cleared flow cache")}
                errorMessage=${msg("Failed to delete flow cache")}
                action=${msg("Clear Cache")}
                .onConfirm=${() => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsInstancesCacheClearCreate();
                }}
            >
                <span slot="header">${msg("Clear Flow cache")}</span>
                <p slot="body">
                    ${msg(
                        `Are you sure you want to clear the flow cache?
            This will cause all flows to be re-evaluated on their next usage.`,
                    )}
                </p>
                <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                    ${msg("Clear cache")}
                </button>
                <div slot="modal"></div>
            </ak-forms-confirm>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-list": FlowListPage;
    }
}
