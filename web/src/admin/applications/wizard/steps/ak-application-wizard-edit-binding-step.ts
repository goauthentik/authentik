import { ApplicationWizardStep } from "@goauthentik/admin/applications/wizard/ApplicationWizardStep.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { groupBy } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-toggle-group";
import { type NavigableButton, type WizardButton } from "@goauthentik/components/ak-wizard/types";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";
import { type SearchSelectBase } from "@goauthentik/elements/forms/SearchSelect/SearchSelect.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select-ez.js";
import { ISearchSelectApi } from "@goauthentik/elements/forms/SearchSelect/ak-search-select-ez.js";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, query, state } from "lit/decorators.js";

import { CoreApi, Group, PoliciesApi, Policy, PolicyBinding, User } from "@goauthentik/api";

const withQuery = <T>(search: string | undefined, args: T) => (search ? { ...args, search } : args);

type SearchConfig = ISearchSelectApi<Policy> | ISearchSelectApi<Group> | ISearchSelectApi<User>;

enum target {
    policy = "policy",
    group = "group",
    user = "user",
}

const policyObjectKeys: Record<target, keyof PolicyBinding> = {
    [target.policy]: "policyObj",
    [target.group]: "groupObj",
    [target.user]: "userObj",
};

const PASS_FAIL = [
    [msg("Pass"), true, false],
    [msg("Don't Pass"), false, true],
].map(([label, value, d]) => ({ label, value, default: d }));

@customElement("ak-application-wizard-edit-binding-step")
export class ApplicationWizardEditBindingStep extends ApplicationWizardStep {
    label = msg("Edit Binding");

    hide = true;

    @query("form#bindingform")
    form!: HTMLFormElement;

    @query(".policy-search-select")
    searchSelect!: SearchSelectBase<Policy> | SearchSelectBase<Group> | SearchSelectBase<User>;

    @state()
    policyGroupUser: target = target.policy;

    instanceId = -1;

    instance?: PolicyBinding;

    get buttons(): WizardButton[] {
        return [
            { kind: "next", label: msg("Save Binding"), destination: "bindings" },
            { kind: "back", destination: "bindings" },
            { kind: "cancel" },
        ];
    }

    override handleButton(button: NavigableButton) {
        if (button.kind === "next") {
            if (!this.form.checkValidity()) {
                return;
            }
            const policyObject = this.searchSelect.selectedObject;
            const policyKey = policyObjectKeys[this.policyGroupUser];
            const newBinding: PolicyBinding = {
                ...(this.formValues as unknown as PolicyBinding),
                [policyKey]: policyObject,
            };

            const bindings = [...(this.wizard.bindings ?? [])];

            if (this.instanceId === -1) {
                bindings.push(newBinding);
            } else {
                bindings[this.instanceId] = newBinding;
            }

            this.instanceId = -1;
            this.handleUpdate({ bindings }, "bindings");
            return;
        }
        super.handleButton(button);
    }

    // The search select configurations for the three different types of fetches that we care about,
    // policy, user, and group, all using the SearchSelectEZ protocol.
    get searchSelectConfigs() {
        return {
            policySelect: {
                fetchObjects: async (query?: string): Promise<Policy[]> => {
                    const policies = await new PoliciesApi(DEFAULT_CONFIG).policiesAllList(
                        withQuery(query, {
                            ordering: "name",
                        }),
                    );
                    return policies.results;
                },
                groupBy: (items: Policy[]) => groupBy(items, (policy) => policy.verboseNamePlural),
                renderElement: (policy: Policy): string => policy.name,
                value: (policy: Policy | undefined): string | undefined => policy?.pk,
                selected: (policy: Policy): boolean => policy.pk === this.instance?.policy,
            },
            groupSelect: {
                fetchObjects: async (query?: string): Promise<Group[]> => {
                    const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(
                        withQuery(query, {
                            ordering: "name",
                            includeUsers: false,
                        }),
                    );
                    return groups.results;
                },
                renderElement: (group: Group): string => group.name,
                value: (group: Group | undefined): string | undefined => group?.pk,
                selected: (group: Group): boolean => group.pk === this.instance?.group,
            },
            userSelect: {
                fetchObjects: async (query?: string): Promise<User[]> => {
                    const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(
                        withQuery(query, {
                            ordering: "username",
                        }),
                    );
                    return users.results;
                },
                renderElement: (user: User): string => user.username,
                renderDescription: (user: User) => html`${user.name}`,
                value: (user: User | undefined): number | undefined => user?.pk,
                selected: (user: User): boolean => user.pk === this.instance?.user,
            },
        };
    }

    renderSearch(title: string, config: SearchConfig, policyKind: target) {
        return this.policyGroupUser === policyKind
            ? html`<ak-form-element-horizontal
                  label=${title}
                  name=${policyKind}
                  ?hidden=${this.policyGroupUser !== policyKind}
              >
                  <ak-search-select-ez
                      .config=${config}
                      class="policy-search-select"
                      blankable
                  ></ak-search-select-ez>
              </ak-form-element-horizontal>`
            : nothing;
    }

    renderForm(instance?: PolicyBinding) {
        const { policySelect, groupSelect, userSelect } = this.searchSelectConfigs;

        return html` <form id="bindingform" class="pf-c-form pf-m-horizontal" slot="form">
            <div class="pf-c-card__body">
                <ak-toggle-group
                    value=${this.policyGroupUser}
                    @ak-toggle=${(ev: CustomEvent<{ value: target }>) => {
                        this.policyGroupUser = ev.detail.value;
                    }}
                >
                    <option value=${target.policy}>${msg("Policy")}</option>
                    <option value=${target.group}>${msg("Group")}</option>
                    <option value=${target.user}>${msg("User")}</option>
                </ak-toggle-group>
            </div>
            <div class="pf-c-card__footer">
                ${this.renderSearch(msg("Policy"), policySelect, target.policy)}
                ${this.renderSearch(msg("Group"), groupSelect, target.group)}
                ${this.renderSearch(msg("User"), userSelect, target.user)}
            </div>
            <ak-switch-input
                name="enabled"
                ?checked=${instance?.enabled ?? true}
                label=${msg("Enabled")}
            ></ak-switch-input>
            <ak-switch-input
                name="negate"
                ?checked=${instance?.negate ?? false}
                label=${msg("Negate result")}
                help=${msg("Negates the outcome of the binding. Messages are unaffected.")}
            ></ak-switch-input>
            <ak-number-input
                label=${msg("Order")}
                name="order"
                value="${instance?.order ?? 0}"
                required
            ></ak-number-input>
            <ak-number-input
                label=${msg("Timeout")}
                name="timeout"
                value="${instance?.timeout ?? 30}"
                required
            ></ak-number-input>
            <ak-radio-input
                name="failureResult"
                label=${msg("Failure result")}
                .options=${PASS_FAIL}
            ></ak-radio-input>
        </form>`;
    }

    renderMain() {
        if (!(this.wizard.bindings && this.wizard.errors)) {
            throw new Error("Application Step received uninitialized wizard context.");
        }
        const currentBinding = this.wizard.currentBinding ?? -1;
        if (this.instanceId !== currentBinding) {
            this.instanceId = currentBinding;
            this.instance =
                this.instanceId === -1 ? undefined : this.wizard.bindings[this.instanceId];
        }
        return this.renderForm(this.instance);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-edit-binding-step": ApplicationWizardEditBindingStep;
    }
}
