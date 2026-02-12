import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/ak-list-select/ak-list-select";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-number-input";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { DataProvision, DualSelectPair } from "#elements/ak-dual-select/types";
import { ModelForm } from "#elements/forms/ModelForm";
import { RadioChangeEventDetail, RadioOption } from "#elements/forms/Radio";
import type SearchSelect from "#elements/forms/SearchSelect/SearchSelect";
import { SlottedTemplateResult } from "#elements/types";

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

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement, state } from "lit/decorators.js";
import { keyed } from "lit/directives/keyed.js";
import { createRef, ref } from "lit/directives/ref.js";

type TargetObject = Application | Group | Role;

function userToPair(item: ReviewerUser): DualSelectPair {
    return [item.uuid, html`<div class="selection-main">${item.name}</div>`, item.name];
}

function groupToPair(item: ReviewerGroup): DualSelectPair {
    return [item.pk, html`<div class="selection-main">${item.name}</div>`, item.name];
}

function createContentTypeOptions(): RadioOption<ContentTypeEnum>[] {
    return [
        {
            value: ContentTypeEnum.AuthentikCoreApplication,
            label: msg("Application"),
            default: true,
        },
        {
            value: ContentTypeEnum.AuthentikCoreGroup,
            label: msg("Group"),
        },
        {
            value: ContentTypeEnum.AuthentikRbacRole,
            label: msg("Role"),
        },
    ] satisfies RadioOption<ContentTypeEnum>[];
}

function formatContentTypePlaceholder(contentType: ContentTypeEnum): string {
    switch (contentType) {
        case ContentTypeEnum.AuthentikCoreApplication:
            return msg("Select an application...");
        case ContentTypeEnum.AuthentikCoreGroup:
            return msg("Select a group...");
        case ContentTypeEnum.AuthentikRbacRole:
            return msg("Select a role...");
        case ContentTypeEnum.UnknownDefaultOpenApi:
            return msg("Select an object...");
    }
}

@customElement("ak-lifecycle-rule-form")
export class LifecycleRuleForm extends ModelForm<LifecycleRule, string> {
    #targetSelectRef = createRef<SearchSelect<TargetObject>>();
    #reviewerGroupsSelectRef = createRef<SearchSelect<Group>>();
    #reviewerUsersSelectRef = createRef<SearchSelect<Group>>();

    #coreApi = new CoreApi(DEFAULT_CONFIG);
    #lifecycleApi = new LifecycleApi(DEFAULT_CONFIG);
    #rbacApi = new RbacApi(DEFAULT_CONFIG);

    @state()
    protected selectedContentType: ContentTypeEnum = ContentTypeEnum.AuthentikCoreApplication;

    protected async loadInstance(pk: string): Promise<LifecycleRule> {
        const rule = await this.#lifecycleApi.lifecycleRulesRetrieve({
            id: pk,
        });

        this.selectedContentType = rule.contentType;

        return rule;
    }

    #fetchGroups = (page: number, search?: string): Promise<DataProvision> => {
        return this.#coreApi
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
        return this.#coreApi
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

    protected override async send(data: LifecycleRule): Promise<LifecycleRule> {
        if (this.instance) {
            return this.#lifecycleApi.lifecycleRulesUpdate({
                id: this.instance.id,
                lifecycleRuleRequest: data,
            });
        }

        return this.#lifecycleApi.lifecycleRulesCreate({
            lifecycleRuleRequest: data,
        });
    }

    protected override serialize(): LifecycleRule | null {
        const result = super.serialize();

        if (!result) {
            return null;
        }

        if (!result.objectId) {
            result.objectId = null;
        }

        return result;
    }

    #loadObjects = async (query?: string): Promise<TargetObject[]> => {
        const promise = match(this.selectedContentType)
            .with(ContentTypeEnum.AuthentikCoreApplication, () =>
                this.#coreApi.coreApplicationsList({
                    ordering: "name",
                    search: query,
                    superuserFullList: true,
                }),
            )
            .with(ContentTypeEnum.AuthentikCoreGroup, () =>
                this.#coreApi.coreGroupsList({
                    ordering: "name",
                    search: query,
                }),
            )
            .with(ContentTypeEnum.AuthentikRbacRole, () =>
                this.#rbacApi.rbacRolesList({
                    ordering: "name",
                    search: query,
                }),
            )
            .otherwise(() => null);

        if (!promise) {
            return [];
        }

        return promise.then((response) => response.results);
    };

    #contentTypeChangeListener = async (
        event: CustomEvent<RadioChangeEventDetail<ContentTypeEnum>>,
    ): Promise<void> => {
        this.selectedContentType = event.detail.value;
    };

    protected renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                label=${msg("Rule Name")}
                name="name"
                required
                value="${ifDefined(this.instance?.name)}"
                placeholder=${msg("Type a name for this lifecycle rule...")}
            ></ak-text-input>

            ${this.renderContentTypeOptions()} ${this.renderTargetSelection()}

            <ak-text-input
                label=${msg("Interval")}
                name="interval"
                required
                value="${this.instance?.interval || "days=60"}"
                input-hint="code"
                help=${msg("The interval between opening new reviews for matching objects.")}
                .bighelp=${html`<ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            ></ak-text-input>

            <ak-text-input
                label=${msg("Grace period")}
                name="gracePeriod"
                required
                value="${this.instance?.gracePeriod || "days=30"}"
                input-hint="code"
                help=${msg("The duration of time before an open review is considered overdue.")}
                .bighelp=${html`<ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            ></ak-text-input>

            <ak-form-element-horizontal label=${msg("Reviewer groups")} name="reviewerGroups">
                ${this.renderReviewerGroupsSelection()}
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
                .help=${msg(
                    html`If checked, approving a review will require at least that many users from
                        <em>each</em> of the selected groups. When disabled, the value is a total
                        across all groups.`,
                )}
            >
            </ak-switch-input>

            <ak-form-element-horizontal label=${msg("Reviewers")} name="reviewers">
                ${this.renderReviewerUserSelection()}
            </ak-form-element-horizontal>
            ${this.renderTransportsSelection()} `;
    }

    protected renderContentTypeOptions(): SlottedTemplateResult {
        return html`<ak-radio-input
            @change=${this.#contentTypeChangeListener}
            label=${msg("Object type")}
            name="contentType"
            required
            .value=${this.instance?.contentType}
            .options=${createContentTypeOptions()}
        ></ak-radio-input>`;
    }

    protected renderTargetSelection() {
        return keyed(
            this.selectedContentType,
            html`<ak-form-element-horizontal label=${msg("Object")} name="objectId">
                <ak-search-select
                    ${ref(this.#targetSelectRef)}
                    placeholder=${formatContentTypePlaceholder(this.selectedContentType)}
                    .fetchObjects=${this.#loadObjects}
                    .renderElement=${(obj: TargetObject) => obj.name}
                    .value=${(obj?: TargetObject) => obj?.pk}
                    .selected=${(obj: TargetObject): boolean => {
                        return obj.pk === this.instance?.objectId;
                    }}
                    blankable
                ></ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When set, the rule will apply to the selected individual object. Otherwise, the rule applies to all objects of the selected type.",
                    )}
                </p>
            </ak-form-element-horizontal>`,
        );
    }

    protected renderReviewerGroupsSelection(): SlottedTemplateResult {
        return html`<ak-dual-select-provider
            ${ref(this.#reviewerGroupsSelectRef)}
            .provider=${this.#fetchGroups}
            .selected=${(this.instance?.reviewerGroupsObj ?? []).map(groupToPair)}
            available-label=${msg("Available Groups")}
            selected-label=${msg("Selected Groups")}
        ></ak-dual-select-provider>`;
    }

    protected renderReviewerUserSelection(): SlottedTemplateResult {
        return html`<ak-dual-select-provider
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
            </p>`;
    }

    protected renderTransportsSelection(): SlottedTemplateResult {
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
                    ${msg("Select which transports should be used to notify the user.")}
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
