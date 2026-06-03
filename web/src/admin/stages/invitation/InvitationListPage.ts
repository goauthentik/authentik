import "#admin/rbac/ObjectPermissionModal";
import "#admin/stages/invitation/InvitationForm";
import "#admin/stages/invitation/InvitationListLink";
import "#admin/stages/invitation/wizard/InvitationWizard";
import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButton, modalInvoker } from "#elements/dialogs";
import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";

import { InvitationForm } from "#admin/stages/invitation/InvitationForm";
import { InvitationWizard } from "#admin/stages/invitation/wizard/InvitationWizard";

import { FlowDesignationEnum, Invitation, ModelEnum, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-stage-invitation-list")
export class InvitationListPage extends TablePage<Invitation> {
    public static styles: CSSResult[] = [...super.styles, PFBanner];

    protected override searchEnabled = true;

    public override pageTitle = msg("Invitations");
    public override pageDescription = msg(
        "Create Invitation Links to enroll Users, and optionally force specific attributes of their account.",
    );
    public override pageIcon = "pf-icon pf-icon-migration";

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override expandable = true;
    public override searchPlaceholder = msg("Search for an invitation by name...");

    public override order = "expires";

    @state()
    protected invitationStageExists = false;

    @state()
    protected multipleEnrollmentFlows = false;

    protected override async apiEndpoint(): Promise<PaginatedResponse<Invitation>> {
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

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Created by"), "created_by"],
        [msg("Expiry")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Invitation(s)")}
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

    protected override row(item: Invitation): SlottedTemplateResult[] {
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
                    : null}`,
            html`<div>
                    <a href="#/identity/users/${item.createdBy.pk}">${item.createdBy.username}</a>
                </div>
                <small>${item.createdBy.name}</small>`,
            item.expires?.toLocaleString() || msg("-"),
            html`${IconEditButton(InvitationForm, item.pk)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikStagesInvitationInvitation}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    protected override renderExpanded(item: Invitation): SlottedTemplateResult {
        return html`<ak-stage-invitation-list-link
            .invitation=${item}
        ></ak-stage-invitation-list-link>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return html`${this.renderNewInvitationDropdown()}`;
    }

    protected renderNewInvitationDropdown(): TemplateResult {
        return html`<ak-dropdown class="pf-c-dropdown">
            <div class="pf-c-dropdown__toggle pf-m-primary pf-m-split-button pf-m-action">
                <button
                    class="pf-c-dropdown__toggle-button"
                    type="button"
                    ${modalInvoker(InvitationWizard, { mode: "existing" })}
                >
                    ${msg("New Invitation")}
                </button>
                <button
                    class="pf-c-dropdown__toggle-button"
                    type="button"
                    id="new-invitation-toggle"
                    aria-haspopup="menu"
                    aria-controls="new-invitation-menu"
                    tabindex="0"
                    aria-label=${msg("New Invitation options")}
                >
                    <i class="fas fa-caret-down" aria-hidden="true"></i>
                </button>
            </div>
            <menu
                class="pf-c-dropdown__menu"
                hidden
                id="new-invitation-menu"
                aria-labelledby="new-invitation-toggle"
                tabindex="-1"
            >
                <li role="presentation">
                    <button
                        type="button"
                        role="menuitem"
                        class="pf-c-dropdown__menu-item"
                        ${modalInvoker(InvitationWizard, { mode: "existing" })}
                        aria-description=${msg(
                            "Opens the new invitation wizard and binds the invitation to an existing enrollment flow.",
                        )}
                    >
                        ${msg("with Existing Enrollment Flow...")}
                    </button>
                </li>
                <li role="presentation">
                    <button
                        type="button"
                        role="menuitem"
                        class="pf-c-dropdown__menu-item"
                        ${modalInvoker(InvitationWizard, { mode: "create" })}
                        aria-description=${msg(
                            "Opens the new invitation wizard, which will create a new enrollment flow and invitation stage.",
                        )}
                    >
                        ${msg("with New Enrollment Flow and Invitation Stage...")}
                    </button>
                </li>
            </menu>
        </ak-dropdown>`;
    }

    protected override render(): SlottedTemplateResult {
        return html`${this.invitationStageExists
                ? null
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

    public override updated(changed: PropertyValues<this>) {
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
