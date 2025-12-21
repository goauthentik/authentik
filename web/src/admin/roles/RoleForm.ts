import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { RbacApi, Role } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-role-form")
export class RoleForm extends ModelForm<Role, string> {
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

    renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Name")} required name="name">
            <input
                type="text"
                value="${ifDefined(this.instance?.name)}"
                class="pf-c-form-control"
                required
            />
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-role-form": RoleForm;
    }
}
