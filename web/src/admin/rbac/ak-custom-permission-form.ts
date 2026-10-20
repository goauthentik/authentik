import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/ak-search-select";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SearchSelectSource } from "#elements/forms/SearchSelect/shared";

import { CustomPermission, ModelEnum, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

// The model where permissions about authentik as a whole belong. It is not exported by authentik.
const SYSTEM_PERMISSION = "authentik_rbac.systempermission";

const MODELS: SearchSelectSource<string> = {
    fetchObjects: async (query?: string) =>
        [
            ...new Set([
                ...Object.values(ModelEnum).filter((model) => model.includes(".")),
                SYSTEM_PERMISSION,
            ]),
        ].filter((model) => !query || model.includes(query.toLowerCase())),
    keyOf: (model) => model,
    labelOf: (model) => model,
};

@customElement("ak-custom-permission-form")
export class CustomPermissionForm extends ModelForm<CustomPermission, string> {
    public static override verboseName = msg("Custom Permission");
    public static override verboseNamePlural = msg("Custom Permissions");

    protected endpoints = {
        load: (pk: string) => aki(RbacApi).rbacCustomPermissionsRetrieve({ id: Number(pk) }),
        create: (customPermissionRequest: CustomPermission) =>
            aki(RbacApi).rbacCustomPermissionsCreate({ customPermissionRequest }),
        update: (pk: string, patchedCustomPermissionRequest: CustomPermission) =>
            aki(RbacApi).rbacCustomPermissionsPartialUpdate({
                id: Number(pk),
                patchedCustomPermissionRequest,
            }),
    };

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated custom permission.")
            : msg("Successfully created custom permission.");
    }

    protected override renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Model")} required name="model">
                <ak-search-select
                    name="model"
                    .source=${MODELS}
                    .value=${this.instance?.model ?? ""}
                    ?readonly=${!!this.instance}
                    required
                    placeholder=${msg("Search for a model...")}
                ></ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The model the permission applies to. Use authentik_rbac.systempermission for permissions about authentik as a whole. It cannot be changed later.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-text-input
                label=${msg("Codename")}
                required
                name="codename"
                value=${this.instance?.codename ?? "custom_"}
                help=${msg(
                    "Starts with custom_, followed by lowercase letters, digits and underscores. It cannot be changed later.",
                )}
            >
            </ak-text-input>
            <ak-text-input
                label=${msg("Name")}
                required
                name="name"
                value="${ifDefined(this.instance?.name)}"
            >
            </ak-text-input>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-custom-permission-form": CustomPermissionForm;
    }
}
