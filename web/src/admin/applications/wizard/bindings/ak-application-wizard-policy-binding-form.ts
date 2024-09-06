import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { groupBy } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-toggle-group";
import { AKElement } from "@goauthentik/elements/Base.js";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import { ISearchSelectApi } from "@goauthentik/elements/forms/SearchSelect/ak-search-select-ez.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select-ez.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CoreApi, Group, PoliciesApi, Policy, PolicyBinding, User } from "@goauthentik/api";

import BasePanel from "../BasePanel";

export class BindingFormStep implements WizardStep {
    id = "binding-form";
    label = msg("Bind A Policy / User / Group");
    disabled = false;

    // Always valid; it's just a list of
    valid = true;

    get buttons(): WizardButton[] {
        return [
            { kind: "next", label: msg("Save"), destination: "binding-choice" },
            { kind: "back", destination: "binding-choice" },
            { kind: "cancel" },
        ];
    }

    render() {
        return html`<ak-application-wizard-binding-choice
            .step=${this}
        ></ak-application-wizard-binding-choice>`;
    }
}

const withQuery = <T>(search: string | undefined, args: T) => (search ? { ...args, search } : args);

type SearchConfig = ISearchSelectApi<Policy> | ISearchSelectApi<Group> | ISearchSelectApi<User>;

enum target {
    policy = "policy",
    group = "group",
    user = "user",
}

const PASS_FAIL = [
    [msg("Pass"), true, false],
    [msg("Don't Pass"), false, true],
].map(([label, value, d]) => ({ label, value, default: d }));

@customElement("ak-application-wizard-policy-binding-form")
export class PolicyBindingFormView extends BasePanel {
    static get styles() {
        return [PFBase, PFCard, PFButton, PFForm, PFAlert, PFInputGroup, PFFormControl, PFSwitch];
    }

    @state()
    policyGroupUser: target = target.policy;

    @property({ type: Object, attribute: false })
    instance?: PolicyBinding;

    @state()
    defaultOrder = 0;

    get policySearchConfig() {
        return {
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
        };
    }

    get groupSearchConfig() {
        return {
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
        };
    }

    get userSearchConfig() {
        return {
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
        };
    }

    renderModeSelector() {
        return html` <ak-toggle-group
            value=${this.policyGroupUser}
            @ak-toggle=${(ev: CustomEvent<{ value: target }>) => {
                this.policyGroupUser = ev.detail.value;
            }}
        >
            <option value=${target.policy}>${msg("Policy")}</option>
            <option value=${target.group}>${msg("Group")}</option>
            <option value=${target.user}>${msg("User")}</option>
        </ak-toggle-group>`;
    }

    renderSearch(title: string, name: string, config: SearchConfig, policyKind: target) {
        return html`<ak-form-element-horizontal
            label=${title}
            name="policy"
            ?hidden=${this.policyGroupUser !== policyKind}
        >
            <ak-search-select-ez .config=${config} blankable></ak-search-select-ez>
        </ak-form-element-horizontal>`;
    }

    render() {
        return html` 
            <div class="pf-c-card__body">${this.renderModeSelector()}</div>
            <div class="pf-c-card__footer">
                ${this.renderSearch(
                    msg("Policy"),
                    "policy",
                    this.policySearchConfig,
                    target.policy,
                )}
                ${this.renderSearch(msg("Group"), "group", this.groupSearchConfig, target.group)}
                ${this.renderSearch(msg("User"), "user", this.userSearchConfig, target.user)}
            </div>
            <ak-switch-input
                name="enabled"
                ?checked=${this.instance?.enabled ?? true}
                label=${msg("Enabled")}
            ></ak-switch-input>
            <ak-switch-input
                name="negate"
                ?checked=${this.instance?.negate ?? false}
                label=${msg("Negate result")}
                help=${msg("Negates the outcome of the binding. Messages are unaffected.")}
            ></ak-switch-input>
            <ak-number-input
                label=${msg("Order")}
                name="order"
                value="${this.instance?.order ?? this.defaultOrder}"
                required
            ></ak-number-input>
            <ak-number-input
                label=${msg("Timeout")}
                name="timeout"
                value="${this.instance?.timeout ?? 30}"
                required
            ></ak-number-input>
            <ak-radio-input
                name="failureResult"
                label=${msg("Failure result")}
                .options=${PASS_FAIL}
            ></ak-radio-input>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-policy-binding-form": PolicyBindingFormView;
    }
}
