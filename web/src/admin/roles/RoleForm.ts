import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { RbacApi, Role } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-role-form")
export class RoleForm extends ModelForm<Role, string> {
    protected override entitySingular = msg("Role");
    protected override entityPlural = msg("Roles");

    loadInstance(pk: string): Promise<Role> {
        return new RbacApi(DEFAULT_CONFIG).rbacRolesRetrieve({
            uuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated role.")
            : msg("Successfully created role.");
    }

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

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
            autofocus
            label=${msg("Role Name")}
            placeholder=${msg("Type a name for this role...")}
            help=${msg("This name will be used to identify the role within authentik.")}
            required
            name="name"
            value="${ifDefined(this.instance?.name)}"
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-role-form": RoleForm;
    }
}
