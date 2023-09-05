import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-toggle-group";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, UserObjectPermission } from "@goauthentik/api";

@customElement("ak-rbac-object-permission-form")
export class ObjectPermissionForm extends ModelForm<UserObjectPermission, number> {
    async loadInstance(pk: number): Promise<UserObjectPermission> {
        return new CoreApi(DEFAULT_CONFIG).coreRbacObjectUserRetrieve({
            id: pk,
        });
    }

    @property()
    targetPk?: string;

    getSuccessMessage(): string {
        if (this.instance?.id) {
            return msg("Successfully updated permission.");
        } else {
            return msg("Successfully created permission.");
        }
    }

    send(data: UserObjectPermission): Promise<unknown> {
        if (this.instance?.id) {
            return new CoreApi(DEFAULT_CONFIG).coreRbacObjectUserUpdate({
                id: this.instance.id,
                userObjectPermissionRequest: data,
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreRbacObjectUserCreate({
                userObjectPermissionRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal name="enabled">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Enabled")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="negate">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.negate, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Negate result")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("Negates the outcome of the binding. Messages are unaffected.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Order")} ?required=${true} name="order">
                <input
                    type="number"
                    value="${first(this.instance?.order, this.defaultOrder)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Timeout")} ?required=${true} name="timeout">
                <input
                    type="number"
                    value="${first(this.instance?.timeout, 30)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="failureResult" label=${msg("Failure result")}>
                <ak-radio
                    .options=${[
                        {
                            label: msg("Pass"),
                            value: true,
                        },
                        {
                            label: msg("Don't pass"),
                            value: false,
                            default: true,
                        },
                    ]}
                    .value=${this.instance?.failureResult}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${msg("Result used when policy execution fails.")}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
