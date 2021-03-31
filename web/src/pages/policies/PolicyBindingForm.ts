import { CoreApi, PoliciesApi, Policy, PolicyBinding } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import { groupBy } from "../../utils";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-policy-binding-form")
export class PolicyBindingForm extends Form<PolicyBinding> {

    @property({attribute: false})
    binding?: PolicyBinding;

    @property()
    targetPk?: string;

    getSuccessMessage(): string {
        if (this.binding) {
            return gettext("Successfully updated binding.");
        } else {
            return gettext("Successfully created binding.");
        }
    }

    async customValidate(form: PolicyBinding): Promise<PolicyBinding> {
        return form;
    }

    send = (data: PolicyBinding): Promise<PolicyBinding> => {
        if (this.binding) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsUpdate({
                policyBindingUuid: this.binding.pk || "",
                data: data
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsCreate({
                data: data
            });
        }
    };

    groupPolicies(policies: Policy[]): TemplateResult {
        return html`
            ${groupBy<Policy>(policies, (p => p.verboseName || "")).map(([group, policies]) => {
                return html`<optgroup label=${group}>
                    ${policies.map(p => {
                        const selected = (this.binding?.policy === p.pk);
                        return html`<option ?selected=${selected} value=${ifDefined(p.pk)}>${p.name}</option>`;
                    })}
                </optgroup>`;
            })}
        `;
    }

    getOrder(): Promise<number> {
        if (this.binding) {
            return Promise.resolve(this.binding.order);
        }
        return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsList({
            target: this.targetPk || "",
        }).then(bindings => {
            const orders = bindings.results.map(binding => binding.order);
            return Math.max(...orders) + 1;
        });
    }


    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Policy")}
                name="policy">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.binding?.policy === undefined}>---------</option>
                    ${until(new PoliciesApi(DEFAULT_CONFIG).policiesAllList({
                        ordering: "pk"
                    }).then(policies => {
                        return this.groupPolicies(policies.results);
                    }), html``)}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Group")}
                name="group">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.binding?.group === undefined}>---------</option>
                    ${until(new CoreApi(DEFAULT_CONFIG).coreGroupsList({
                        ordering: "pk"
                    }).then(groups => {
                        return groups.results.map(group => {
                            return html`<option value=${ifDefined(group.pk)} ?selected=${group.pk === this.binding?.group}>${group.name}</option>`;
                        });
                    }), html``)}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("User")}
                name="user">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.binding?.user === undefined}>---------</option>
                    ${until(new CoreApi(DEFAULT_CONFIG).coreUsersList({
                        ordering: "pk"
                    }).then(users => {
                        return users.results.map(user => {
                            return html`<option value=${ifDefined(user.pk)} ?selected=${user.pk === this.binding?.user}>${user.name}</option>`;
                        });
                    }), html``)}
                </select>
            </ak-form-element-horizontal>
            <input required name="target" type="hidden" value=${ifDefined(this.binding?.target || this.targetPk)}>
            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.binding?.enabled || true}>
                    <label class="pf-c-check__label">
                        ${gettext("Enabled")}
                    </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Order")}
                ?required=${true}
                name="order">
                <input type="number" value="${until(this.getOrder(), this.binding?.order)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Timeout")}
                ?required=${true}
                name="timeout">
                <input type="number" value="${this.binding?.timeout || 30}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
        </form>`;
    }

}
