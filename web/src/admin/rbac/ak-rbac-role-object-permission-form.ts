import "#components/ak-switch-input";
import "#elements/ToggleGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { roleSource } from "#admin/common/search-sources";

import { ModelEnum, PaginatedPermissionList, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface RoleAssignData {
    role: string;
    permissions: {
        [key: string]: boolean;
    };
}

@customElement("ak-rbac-role-object-permission-form")
export class RoleObjectPermissionForm extends ModelForm<RoleAssignData, number> {
    public static override verboseName = msg("Role Object Permission");
    public static override verboseNamePlural = msg("Role Object Permissions");
    public static override createLabel = msg("Assign");
    public static override submitVerb = msg("Assign");

    @property({ type: String })
    public model: ModelEnum | null = null;

    @property({
        attribute: "object-pk",
        useDefault: true,
    })
    public objectPk: string | null = null;

    @state()
    protected modelPermissions: PaginatedPermissionList | null = null;

    public override reset(): void {
        super.reset();

        this.modelPermissions = null;
    }

    async load(): Promise<void> {
        const [appLabel, modelName] = (this.model || "").split(".");

        this.modelPermissions = await aki(RbacApi).rbacPermissionsList({
            contentTypeModel: modelName,
            contentTypeAppLabel: appLabel,
            ordering: "codename",
        });
    }

    loadInstance(): Promise<RoleAssignData> {
        throw new Error("Method not implemented.");
    }

    getSuccessMessage(): string {
        return msg("Successfully assigned permission.");
    }

    send(data: RoleAssignData): Promise<unknown> {
        const [app, _model] = this.model?.split(".") || "";

        return aki(RbacApi).rbacPermissionsAssignedByRolesAssign({
            uuid: data.role,
            permissionAssignRequest: {
                permissions: Object.keys(data.permissions)
                    .filter((key) => data.permissions[key])
                    .map((permission) => `${app}.${permission}`),
                model: this.model!,
                objectPk: this.objectPk ?? undefined,
            },
        });
    }

    renderForm(): SlottedTemplateResult {
        if (!this.modelPermissions) {
            return null;
        }

        return html`<span
                >${msg(
                    "Choose the object permissions that you want the selected role to have on this object. These object permissions are in addition to any global permissions already within the role.",
                )}</span
            >
            <form class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${msg("Role")} name="role">
                    ${AKSearchSelect({
                        name: "role",
                        source: roleSource,
                        placeholder: msg("Select a role..."),
                        blankable: false,
                    })}
                </ak-form-element-horizontal>
                ${this.modelPermissions?.results
                    .filter((perm) => {
                        const [_app, model] = this.model?.split(".") || "";

                        return perm.codename !== `add_${model}`;
                    })
                    .map((perm) => {
                        return html`<ak-switch-input
                            name="permissions.${perm.codename}"
                            label=${perm.name}
                        ></ak-switch-input>`;
                    })}
            </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-role-object-permission-form": RoleObjectPermissionForm;
    }
}
