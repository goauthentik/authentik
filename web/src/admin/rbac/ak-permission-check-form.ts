import "#components/ak-text-input";
import "#elements/CodeMirror";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/forms/HorizontalFormElement";
import "#elements/Label";
import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";
import { docLink } from "#common/global";

import { DataProvision, DualSelectPair } from "#elements/ak-dual-select/types";
import { ModelForm } from "#elements/forms/ModelForm";
import { PFColor } from "#elements/Label";

import { PermissionCheck, RbacApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

function bindingPair(id: string, functions?: string, unknownFields?: string[]): DualSelectPair {
    return [
        id,
        html`<div class="selection-main">${id}</div>
            ${functions ? html`<div class="selection-desc">${functions}</div>` : nothing}
            ${
                unknownFields?.length
                    ? html`<ak-label color=${PFColor.Orange} compact>
                          ${msg(str`Paths started with fields it lacks: ${unknownFields.join(", ")}`)}
                      </ak-label>`
                    : nothing
            }`,
        `${id} ${functions ?? ""}`,
    ];
}

function matching(pairs: DualSelectPair[], search?: string): DataProvision {
    const term = (search ?? "").toLowerCase();

    return {
        options: pairs.filter((pair) =>
            String(pair[2] ?? pair[0])
                .toLowerCase()
                .includes(term),
        ),
    };
}

@customElement("ak-permission-check-form")
export class PermissionCheckForm extends ModelForm<PermissionCheck, string> {
    public static override verboseName = msg("Permission Check");
    public static override verboseNamePlural = msg("Permission Checks");

    public override size = PFSize.XLarge;

    protected endpoints = {
        load: (checkUuid: string) => aki(RbacApi).rbacPermissionChecksRetrieve({ checkUuid }),
        create: (permissionCheckRequest: PermissionCheck) =>
            aki(RbacApi).rbacPermissionChecksCreate({ permissionCheckRequest }),
        update: (checkUuid: string, patchedPermissionCheckRequest: PermissionCheck) =>
            aki(RbacApi).rbacPermissionChecksPartialUpdate({
                checkUuid,
                patchedPermissionCheckRequest,
            }),
    };

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated permission check.")
            : msg("Successfully created permission check.");
    }

    protected async endpointOptions(_page: number, search?: string): Promise<DataProvision> {
        const endpoints = await aki(RbacApi).rbacEndpointsList();

        return matching(
            endpoints.map((endpoint) => bindingPair(endpoint.id, endpoint.functions.join(", "))),
            search,
        );
    }

    protected override renderForm(): TemplateResult {
        const selected = (this.instance?.endpoints ?? []).map((id) =>
            bindingPair(id, undefined, this.instance?.unknownFields[id]),
        );

        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-text-input
                label=${msg("Name")}
                required
                name="name"
                value="${ifDefined(this.instance?.name)}"
            >
            </ak-text-input>
            <ak-form-element-horizontal label=${msg("Endpoints")} required name="endpoints">
                <ak-dual-select-provider
                    .provider=${(page: number, search?: string) => this.endpointOptions(page, search)}
                    .selected=${selected}
                    available-label=${msg("Available")}
                    selected-label=${msg("Bound")}
                ></ak-dual-select-provider>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "API endpoints this check decides on, like core/users:list. An endpoint can be bound to one check only.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Expression")} required name="expression">
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.expression)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Python code defining permission checks.")}
                    <a
                        target="_blank"
                        rel="noopener noreferrer"
                        href=${docLink("/users-sources/access-control/custom_permissions#examples")}
                    >
                        ${msg("See examples in the documentation.")}
                    </a>
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-permission-check-form": PermissionCheckForm;
    }
}
