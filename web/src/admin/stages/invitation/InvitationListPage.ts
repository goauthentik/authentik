import "@goauthentik/admin/stages/invitation/InvitationForm";
import "@goauthentik/admin/stages/invitation/InvitationListLink";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { FlowDesignationEnum, Invitation, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-invitation-list")
export class InvitationListPage extends TablePage<Invitation> {
    expandable = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Invitations");
    }
    pageDescription(): string {
        return msg(
            "Create Invitation Links to enroll Users, and optionally force specific attributes of their account.",
        );
    }
    pageIcon(): string {
        return "pf-icon pf-icon-migration";
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(PFBanner);
    }

    checkbox = true;

    @property()
    order = "expires";

    @state()
    invitationStageExists = false;

    @state()
    multipleEnrollmentFlows = false;

    async apiEndpoint(page: number): Promise<PaginatedResponse<Invitation>> {
        // Check if any invitation stages exist
        const stages = await new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesList({
            noFlows: false,
        });
        this.invitationStageExists = stages.pagination.count > 0;
        this.expandable = this.invitationStageExists;
        stages.results.forEach((stage) => {
            const enrollmentFlows = (stage.flowSet || []).filter(
                (flow) => flow.designation === FlowDesignationEnum.Enrollment,
            );
            if (enrollmentFlows.length > 1) {
                this.multipleEnrollmentFlows = true;
            }
        });
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Created by"), "created_by"),
            new TableColumn(msg("Expiry")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Invitation(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Invitation) => {
                return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsUsedByList({
                    inviteUuid: item.pk,
                });
            }}
            .delete=${(item: Invitation) => {
                return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsDestroy({
                    inviteUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Invitation): TemplateResult[] {
        return [
            html`<div>${item.name}</div>
                ${!item.flowObj && this.multipleEnrollmentFlows
                    ? html`
                          <ak-label color=${PFColor.Orange}>
                              ${msg(
                                  "Invitation not limited to any flow, and can be used with any enrollment flow.",
                              )}
                          </ak-label>
                      `
                    : html``}`,
            html`${item.createdBy?.username}`,
            html`${item.expires?.toLocaleString() || msg("-")}`,
            html` <ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update Invitation")} </span>
                <ak-invitation-form slot="form" .instancePk=${item.pk}> </ak-invitation-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderExpanded(item: Invitation): TemplateResult {
        return html` <td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <ak-stage-invitation-list-link
                        .invitation=${item}
                    ></ak-stage-invitation-list-link>
                </div>
            </td>
            <td></td>
            <td></td>
            <td></td>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Invitation")} </span>
                <ak-invitation-form slot="form"> </ak-invitation-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon=${this.pageIcon()}
                header=${this.pageTitle()}
                description=${ifDefined(this.pageDescription())}
            >
            </ak-page-header>
            ${this.invitationStageExists
                ? html``
                : html`
                      <div class="pf-c-banner pf-m-warning">
                          ${msg(
                              "Warning: No invitation stage is bound to any flow. Invitations will not work as expected.",
                          )}
                      </div>
                  `}
            <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                <div class="pf-c-card">${this.renderTable()}</div>
            </section>`;
    }
}
