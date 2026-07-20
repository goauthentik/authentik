import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-text-input";

import { aki } from "#common/api/client";

import { DataProvision, DualSelectPair } from "#elements/ak-dual-select/types";
import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    ApplicationEntitlement,
    CoreApi,
    CoreApplicationEntitlementsListRequest,
    RequestRule,
    RequestRuleBinding,
    RequestsApi,
    RequestsRulesListRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit-html/directives/if-defined.js";

function entitlementToPair(entitlement: ApplicationEntitlement): DualSelectPair {
    return [entitlement.pbmUuid, entitlement.name, entitlement.name];
}

const CHILD_BINDING_PAGE_SIZE = 100;

@customElement("ak-request-rule-binding-form")
export class RequestRuleBindingForm extends ModelForm<RequestRuleBinding, string> {
    public static override verboseName = msg("Request Rule Binding");
    public static override verboseNamePlural = msg("Request Rule Bindings");

    #coreApi = aki(CoreApi);

    @property({ type: String })
    public targetPk = "";

    @state()
    protected selectedEntitlementPairs: DualSelectPair[] = [];

    protected async loadInstance(pk: string): Promise<RequestRuleBinding> {
        const binding = await aki(RequestsApi).requestsRuleBindingsRetrieve({ uuid: pk });
        await this.#loadChildBindings(pk);
        return binding;
    }

    #loadChildBindings = async (bindingPk: string): Promise<void> => {
        if (!this.targetPk) {
            this.selectedEntitlementPairs = [];
            return;
        }

        const [entitlements, childBindings] = await Promise.all([
            this.#coreApi.coreApplicationEntitlementsList({
                app: this.targetPk,
                ordering: "name",
                pageSize: CHILD_BINDING_PAGE_SIZE,
            }),
            aki(RequestsApi).requestsRuleChildBindingsList({
                binding: bindingPk,
                pageSize: CHILD_BINDING_PAGE_SIZE,
            }),
        ]);

        const entitlementsByPk = new Map(entitlements.results.map((e) => [e.pbmUuid, e]));

        this.selectedEntitlementPairs = childBindings.results
            .map((childBinding) => entitlementsByPk.get(childBinding.target))
            .filter((entitlement): entitlement is ApplicationEntitlement => Boolean(entitlement))
            .map(entitlementToPair);
    };

    #fetchEntitlements = (page: number, search?: string): Promise<DataProvision> => {
        const args: CoreApplicationEntitlementsListRequest = {
            app: this.targetPk,
            ordering: "name",
            page,
            search,
        };
        return this.#coreApi.coreApplicationEntitlementsList(args).then((results) => {
            return {
                pagination: results.pagination,
                options: results.results.map(entitlementToPair),
            };
        });
    };

    protected override async send(
        data: RequestRuleBinding & { relatedTargets?: Array<string | number> },
    ): Promise<RequestRuleBinding> {
        if (this.targetPk) {
            data.target = this.targetPk;
        }
        const relatedTargets = (data.relatedTargets ?? []).map((target) => String(target));

        const binding = this.instance?.uuid
            ? await aki(RequestsApi).requestsRuleBindingsUpdate({
                  uuid: this.instance.uuid,
                  requestRuleBindingRequest: data,
              })
            : await aki(RequestsApi).requestsRuleBindingsCreate({
                  requestRuleBindingRequest: data,
              });

        await this.#reconcileChildBindings(binding.uuid, relatedTargets);

        return binding;
    }

    #reconcileChildBindings = async (
        bindingPk: string | undefined,
        desiredTargets: string[],
    ): Promise<void> => {
        if (!bindingPk) return;

        const existing = await aki(RequestsApi).requestsRuleChildBindingsList({
            binding: bindingPk,
            pageSize: CHILD_BINDING_PAGE_SIZE,
        });

        const desiredSet = new Set(desiredTargets);
        const existingByTarget = new Map(existing.results.map((cb) => [cb.target, cb]));

        await Promise.all([
            ...desiredTargets
                .filter((target) => !existingByTarget.has(target))
                .map((target) =>
                    aki(RequestsApi).requestsRuleChildBindingsCreate({
                        requestRuleChildBindingRequest: { binding: bindingPk, target },
                    }),
                ),
            ...existing.results
                .filter((cb) => !desiredSet.has(cb.target))
                .map((cb) =>
                    aki(RequestsApi).requestsRuleChildBindingsDestroy({ uuid: cb.uuid || "" }),
                ),
        ]);
    };

    protected renderForm(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Rule")} required name="rule">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<RequestRule[]> => {
                        const args: RequestsRulesListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const rules = await aki(RequestsApi).requestsRulesList(args);
                        return rules.results;
                    }}
                    .renderElement=${(rule: RequestRule) => rule.name}
                    .value=${(rule: RequestRule | null) => rule?.uuid}
                    .selected=${(rule: RequestRule) => rule.uuid === this.instance?.rule}
                    blankable
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-text-input
                label=${msg("Pending expiry")}
                name="expiryPending"
                input-hint="code"
                required
                value="${ifDefined(this.instance?.expiryPending ?? "hours=1")}"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                        ${msg(
                            "How long a request against this binding stays pending before it automatically lapses if not approved or denied.",
                        )}
                    </p>
                    <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            >
            </ak-text-input>
            <ak-text-input
                label=${msg("Maximum granted expiry")}
                name="expiryGrantedMax"
                input-hint="code"
                required
                value="${ifDefined(this.instance?.expiryGrantedMax ?? "hours=1")}"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                        ${msg(
                            "The maximum duration a grant approved against this binding can last. Requesters may ask for less, but never more.",
                        )}
                    </p>
                    <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            >
            </ak-text-input>
            ${this.renderEntitlementsSelection()}`;
    }

    protected renderEntitlementsSelection(): SlottedTemplateResult {
        if (!this.targetPk) {
            return nothing;
        }
        return html`<ak-form-element-horizontal
            label=${msg("Additional entitlements")}
            name="relatedTargets"
        >
            <ak-dual-select-provider
                .provider=${this.#fetchEntitlements}
                .selected=${this.selectedEntitlementPairs}
                available-label=${msg("Available entitlements")}
                selected-label=${msg("Granted entitlements")}
            ></ak-dual-select-provider>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "Application entitlements granted alongside access to this object when a request is approved.",
                )}
            </p>
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-request-rule-binding-form": RequestRuleBindingForm;
    }
}
