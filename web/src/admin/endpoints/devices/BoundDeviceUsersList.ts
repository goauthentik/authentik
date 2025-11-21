import "#admin/groups/GroupForm";
import "#admin/rbac/ObjectPermissionModal";
import "#admin/users/UserForm";
import "#components/ak-status-label";
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { PolicyBindingCheckTarget, PolicyBindingCheckTargetToLabel } from "#admin/policies/utils";

import { PoliciesApi, PolicyBinding } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

@customElement("ak-bound-device-users-list")
export class BoundDeviceUsersList extends Table<PolicyBinding> {
    @property()
    target?: string;

    checkbox = true;
    clearOnRefresh = true;

    order = "order";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFSpacing);
    }

    async apiEndpoint(): Promise<PaginatedResponse<PolicyBinding>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsList({
            ...(await this.defaultEndpointConfig()),
            target: this.target || "",
        });
    }

    protected override rowLabel(item: PolicyBinding): string | null {
        return item.order?.toString() ?? null;
    }

    protected columns: TableColumn[] = [
        [
            [PolicyBindingCheckTarget.user, PolicyBindingCheckTarget.group]
                .map((ct) => PolicyBindingCheckTargetToLabel(ct))
                .join(" / "),
        ],
    ];

    getPolicyUserGroupRowLabel(item: PolicyBinding): string {
        if (item.policy) {
            return msg(str`Policy ${item.policyObj?.name}`);
        } else if (item.group) {
            return msg(str`Group ${item.groupObj?.name}`);
        } else if (item.user) {
            return msg(str`User ${item.userObj?.name}`);
        }
        return msg("-");
    }

    getPolicyUserGroupRow(item: PolicyBinding): TemplateResult {
        const label = this.getPolicyUserGroupRowLabel(item);
        if (item.user) {
            return html` <a href=${`#/identity/users/${item.user}`}> ${label} </a> `;
        }
        if (item.group) {
            return html` <a href=${`#/identity/groups/${item.group}`}> ${label} </a> `;
        }
        return html`${label}`;
    }

    row(item: PolicyBinding): SlottedTemplateResult[] {
        return [html`${this.getPolicyUserGroupRow(item)}`];
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-module"
                ><span>${msg("No Users bound.")}</span>
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bound-device-users-list": BoundDeviceUsersList;
    }
}
