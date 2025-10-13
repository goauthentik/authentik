import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { ifPresent } from "#elements/utils/attributes";

import { RbacApi, Role } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-role-form")
export class RoleForm extends ModelForm<Role, string> {
    loadInstance(pk: string): Promise<Role> {
        return new RbacApi(DEFAULT_CONFIG).rbacRolesRetrieve({
            uuid: pk,
        });
    }

    protected override entityLabel = msg("role");

    async send(data: Role): Promise<Role> {
        if (this.instance?.pk) {
            return new RbacApi(DEFAULT_CONFIG).rbacRolesPartialUpdate({
                uuid: this.instance.pk,
                patchedRoleRequest: data,
            });
        }
        return new RbacApi(DEFAULT_CONFIG).rbacRolesCreate({
            roleRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`<ak-text-input
            name="name"
            label=${msg("Role Name")}
            placeholder=${msg("Type a name for this role...")}
            required
            value="${ifPresent(this.instance?.name)}"
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-role-form": RoleForm;
    }
}
