import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/ak-list-select/ak-list-select";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-number-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { DataProvision, DualSelectPair } from "#elements/ak-dual-select/types";
import { ModelForm } from "#elements/forms/ModelForm";
import type SearchSelect from "#elements/forms/SearchSelect/SearchSelect";

import { eventTransportsProvider, eventTransportsSelector } from "#admin/events/RuleFormHelpers";

import {
    Application,
    ContentTypeEnum,
    CoreApi,
    Group,
    LifecycleApi,
    LifecycleRule,
    RbacApi,
    ReviewerGroup,
    ReviewerUser,
    Role,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

type TargetObject = Application | Group | Role;

function userToPair(item: ReviewerUser): DualSelectPair {
    return [item.uuid, html` <div class="selection-main">${item.name}</div>`, item.name];
}

function groupToPair(item: ReviewerGroup): DualSelectPair {
    return [item.pk, html` <div class="selection-main">${item.name}</div>`, item.name];
}

@customElement("ak-lifecycle-rule-form")
export class LifecycleRuleForm extends ModelForm<LifecycleRule, string> {
    #selectedContentType: ContentTypeEnum | undefined;
    #targetSelectRef = createRef<SearchSelect<TargetObject>>();
    #reviewerGroupsSelectRef = createRef<SearchSelect<Group>>();
    #reviewerUsersSelectRef = createRef<SearchSelect<Group>>();

    async loadInstance(pk: string): Promise<LifecycleRule> {
        const rule = await new LifecycleApi(DEFAULT_CONFIG).lifecycleLifecycleRulesRetrieve({
            id: pk,
        });
        this.#selectedContentType = rule.contentType;
        return rule;
    }

    #fetchGroups = (page: number, search?: string): Promise<DataProvision> => {
        return new CoreApi(DEFAULT_CONFIG)
            .coreGroupsList({
                page: page,
                search: search,
            })
            .then((results) => {
                return {
                    pagination: results.pagination,
                    options: results.results.map(groupToPair),
                };
            });
    };

    #fetchUsers = (page: number, search?: string): Promise<DataProvision> => {
        return new CoreApi(DEFAULT_CONFIG)
            .coreUsersList({
                page: page,
                search: search,
            })
            .then((results) => {
                return {
                    pagination: results.pagination,
                    options: results.results.map(userToPair),
                };
            });
    };

    async send(data: LifecycleRule): Promise<LifecycleRule> {
        if (this.instance) {
            return new LifecycleApi(DEFAULT_CONFIG).lifecycleLifecycleRulesUpdate({
                id: this.instance.id || "",
                lifecycleRuleRequest: data,
            });
        }
        return new LifecycleApi(DEFAULT_CONFIG).lifecycleLifecycleRulesCreate({
            lifecycleRuleRequest: data,
        });
    }

    protected serialize(): LifecycleRule | undefined {
        const ret = super.serialize();
        if (ret === undefined) return;
        if (ret.objectId === "") ret.objectId = null;
        return ret;
    }

    private async loadObjects(query?: string): Promise<TargetObject[]> {
        switch (this.#selectedContentType) {
            case ContentTypeEnum.AuthentikCoreApplication:
                return (
                    await new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
                        ordering: "name",
                        search: query,
                    })
                ).results;
            case ContentTypeEnum.AuthentikCoreGroup:
                return (
                    await new CoreApi(DEFAULT_CONFIG).coreGroupsList({
                        ordering: "name",
                        search: query,
                    })
                ).results;
            case ContentTypeEnum.AuthentikRbacRole:
                return (
                    await new RbacApi(DEFAULT_CONFIG).rbacRolesList({
                        ordering: "name",
                        search: query,
                    })
                ).results;
            default:
                return [];
        }
    }

    async #handleContentTypeChange(ev: Event): Promise<void> {
        this.#selectedContentType = (ev.target as HTMLSelectElement).value as ContentTypeEnum;
        await this.#targetSelectRef.value?.updateData();
    }

    renderForm(): TemplateResult {
        return html`
            ${this.#renderTargetSelection()}
            <ak-form-element-horizontal label=${msg("Interval")} name="interval" required>
                <input
                    type="text"
                    value="${this.instance?.interval || "days=60"}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("The interval between opening new reviews for matching objects.")}
                </p>
                <ak-utils-time-delta-help></ak-utils-time-delta-help>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Grace period")} name="gracePeriod" required>
                <input
                    type="text"
                    value="${this.instance?.gracePeriod || "days=30"}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("The duration of time before an open review is considered overdue.")}
                </p>
                <ak-utils-time-delta-help></ak-utils-time-delta-help>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${msg("Reviewer groups")} name="reviewerGroups">
                ${this.#renderReviewerGroupsSelection()}
            </ak-form-element-horizontal>
            <ak-number-input
                label=${msg("Min reviewers")}
                min=${1}
                name="minReviewers"
                value="${this.instance?.minReviewers ?? 1}"
                help=${msg(
                    "Number of users from the selected reviewer groups that must approve the review.",
                )}
            ></ak-number-input>
            <ak-switch-input
                name="minReviewersIsPerGroup"
                ?checked=${this.instance?.minReviewersIsPerGroup ?? false}
                label=${msg("Min reviewers is per-group")}
                help=${msg(
                    "If checked, approving a review will require at least that many users from each of the selected groups.",
                )}
            >
            </ak-switch-input>

            <ak-form-element-horizontal label=${msg("Reviewers")} name="reviewers">
                ${this.#renderReviewerUserSelection()}
            </ak-form-element-horizontal>
            ${this.#renderTransportsSelection()}
        `;
    }

    #renderTargetSelection(): TemplateResult {
        return html` <ak-form-element-horizontal
                label=${msg("Object type")}
                required
                name="contentType"
            >
                <select class="pf-c-form-control" @change=${this.#handleContentTypeChange}>
                    <option value="" ?selected=${this.instance?.contentType === undefined}>
                        ---------
                    </option>
                    <option
                        value=${ContentTypeEnum.AuthentikCoreApplication}
                        ?selected=${this.instance?.contentType ===
                        ContentTypeEnum.AuthentikCoreApplication}
                    >
                        ${msg("Application")}
                    </option>
                    <option
                        value=${ContentTypeEnum.AuthentikCoreGroup}
                        ?selected=${this.instance?.contentType ===
                        ContentTypeEnum.AuthentikCoreGroup}
                    >
                        ${msg("Group")}
                    </option>
                    <option
                        value=${ContentTypeEnum.AuthentikRbacRole}
                        ?selected=${this.instance?.contentType ===
                        ContentTypeEnum.AuthentikRbacRole}
                    >
                        ${msg("Role")}
                    </option>
                </select>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${msg("Object")} name="objectId">
                <ak-search-select
                    ${ref(this.#targetSelectRef)}
                    .fetchObjects=${this.loadObjects.bind(this)}
                    .renderElement=${(obj: TargetObject): string => {
                        return obj.name;
                    }}
                    .value=${(obj: TargetObject | undefined): string | undefined => {
                        return obj?.pk;
                    }}
                    .selected=${(obj: TargetObject): boolean => {
                        return obj.pk === this.instance?.objectId;
                    }}
                    blankable
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When set, the rule will apply to the selected individual object. Otherwise, the rule applies to all objects of the selected type.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }

    #renderReviewerGroupsSelection(): TemplateResult {
        return html`
            <ak-dual-select-provider
                ${ref(this.#reviewerGroupsSelectRef)}
                .provider=${this.#fetchGroups}
                .selected=${(this.instance?.reviewerGroupsObj ?? []).map(groupToPair)}
                available-label=${msg("Available Groups")}
                selected-label=${msg("Selected Groups")}
            ></ak-dual-select-provider>
        `;
    }

    #renderReviewerUserSelection(): TemplateResult {
        return html`
            <ak-dual-select-provider
                ${ref(this.#reviewerUsersSelectRef)}
                .provider=${this.#fetchUsers}
                .selected=${(this.instance?.reviewersObj ?? []).map(userToPair)}
                available-label=${msg("Available Users")}
                selected-label=${msg("Selected Users")}
            ></ak-dual-select-provider>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "A review will require approval from each of the users selected here in addition to group members as per above settings.",
                )}
            </p>
        `;
    }

    #renderTransportsSelection(): TemplateResult {
        return html`
            <ak-form-element-horizontal
                label=${msg("Notification transports")}
                required
                name="notificationTransports"
            >
                <ak-dual-select-dynamic-selected
                    .provider=${eventTransportsProvider}
                    .selector=${eventTransportsSelector(this.instance?.notificationTransports)}
                    available-label="${msg("Available Transports")}"
                    selected-label="${msg("Selected Transports")}"
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select which transports should be used to notify the user. If none are selected, the notification will only be shown in the authentik UI.",
                    )}
                </p>
            </ak-form-element-horizontal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-lifecycle-rule-form": LifecycleRuleForm;
    }
}
