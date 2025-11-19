import "#admin/rbac/ObjectPermissionModal";
import "#admin/stages/invitation/InvitationForm";
import "#admin/stages/invitation/InvitationListLink";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";

import {
    FlowDesignationEnum,
    Invitation,
    RbacPermissionsAssignedByUsersListModelEnum,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, HTMLTemplateResult, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-stage-invitation-list")
export class InvitationListPage extends TablePage<Invitation> {
    expandable = true;

    protected override searchEnabled = true;
    public pageTitle = msg("Invitations");
    public pageDescription = msg(
        "Create Invitation Links to enroll Users, and optionally force specific attributes of their account.",
    );
    public pageIcon = "pf-icon pf-icon-migration";

    static styles: CSSResult[] = [...super.styles, PFBanner];

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "expires";

    @state()
    invitationStageExists = false;

    @state()
    multipleEnrollmentFlows = false;

    async apiEndpoint(): Promise<PaginatedResponse<Invitation>> {
        try {
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
        } catch {
            // assuming we can't fetch stages, ignore the error
        }
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Created by"), "created_by"],
        [msg("Expiry")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

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

    row(item: Invitation): SlottedTemplateResult[] {
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
                    : nothing}`,
            html`<div>
                    <a href="#/identity/users/${item.createdBy.pk}">${item.createdBy.username}</a>
                </div>
                <small>${item.createdBy.name}</small>`,
            html`${item.expires?.toLocaleString() || msg("-")}`,
            html` <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Invitation")}</span>
                    <ak-invitation-form slot="form" .instancePk=${item.pk}> </ak-invitation-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikStagesInvitationInvitation}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderExpanded(item: Invitation): TemplateResult {
        return html`<ak-stage-invitation-list-link
            .invitation=${item}
        ></ak-stage-invitation-list-link>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Invitation")}</span>
                <ak-invitation-form slot="form"> </ak-invitation-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }

    render(): HTMLTemplateResult {
        return html`${this.invitationStageExists
                ? nothing
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

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: this.pageIcon,
            header: this.pageTitle,
            description: this.pageDescription,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-invitation-list": InvitationListPage;
    }
}
