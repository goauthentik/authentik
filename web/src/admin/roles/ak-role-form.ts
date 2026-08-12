import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { ModelForm } from "#elements/forms/ModelForm";

import { RbacApi, Role } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-role-form")
export class RoleForm extends ModelForm<Role, string> {
    public static override verboseName = msg("Role");
    public static override verboseNamePlural = msg("Roles");

    public override size = PFSize.Medium;

    protected endpoints = {
        load: (uuid: string) =>
            aki(RbacApi).rbacRolesRetrieve({
                uuid,
            }),
        create: (roleRequest: Role) =>
            aki(RbacApi).rbacRolesCreate({
                roleRequest,
            }),
        update: (uuid: string, patchedRoleRequest: Role) =>
            aki(RbacApi).rbacRolesPartialUpdate({
                uuid,
                patchedRoleRequest,
            }),
    };

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated role.")
            : msg("Successfully created role.");
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
            autofocus
            spellcheck="false"
            autocomplete="off"
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
