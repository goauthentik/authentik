import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/ak-list-select/ak-list-select";
import "#components/ak-number-input";
import {state} from "lit/decorators.js";

import {DEFAULT_CONFIG} from "#common/api/config";

import {ModelForm} from "#elements/forms/ModelForm";

import {
    Application,
    ContentTypeEnum, CoreApi,
    Group, LifecycleRule, RbacApi, RelatedUser,
    ReviewsApi, Role,
} from "@goauthentik/api";

import {msg} from "@lit/localize";
import {css, html, TemplateResult} from "lit";
import {customElement} from "lit/decorators.js";
import {createRef, ref} from "lit/directives/ref.js";
import type SearchSelect from "#elements/forms/SearchSelect/SearchSelect";
import {DataProvision, DualSelectPair} from "#elements/ak-dual-select/types";
import {coreGroupPair} from "#admin/groups/GroupForm";
import {eventTransportsProvider, eventTransportsSelector} from "#admin/events/RuleFormHelpers";

type TargetObject = Application | Group | Role;

function userToPair(item: RelatedUser): DualSelectPair {
    return [item.uuid, html`
        <div class="selection-main">${item.name}</div>`, item.name];
}

enum ReviewerSelection {
    Groups = "groups",
    Users = "users",
}

@customElement("ak-lifecycle-rule-form")
export class LifecycleRuleForm extends ModelForm<LifecycleRule, string> {
    #selectedContentType: ContentTypeEnum | undefined;
    #targetSelectRef = createRef<SearchSelect<TargetObject>>();
    #reviewerGroupsSelectRef = createRef<SearchSelect<Group>>();
    #reviewerUsersSelectRef = createRef<SearchSelect<Group>>();

    @state()
    protected selectedReviewerSelection: ReviewerSelection = ReviewerSelection.Groups;

    static get styles() {
        return [...super.styles, css`
            .ak-horizontal-radio-select {
                padding-top: var(
                    --pf-c-form--m-horizontal__group-label--md--PaddingTop,
                    var(--pf-global--spacer--form-element)
                );
            }
        `];
    }

    async loadInstance(pk: string): Promise<LifecycleRule> {
        const rule = await new ReviewsApi(DEFAULT_CONFIG).reviewsLifecycleRulesRetrieve({
            id: pk,
        });
        this.#selectedContentType = rule.contentType;
        this.selectedReviewerSelection = rule.reviewers.length > 0 ? ReviewerSelection.Users : ReviewerSelection.Groups;
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
                    options: results.results.map(coreGroupPair),
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
                    options: results.results.map(userToPair)
                }
            })
    }

    async send(data: LifecycleRule): Promise<LifecycleRule> {
        if (this.instance) {
            return new ReviewsApi(DEFAULT_CONFIG).reviewsLifecycleRulesUpdate({
                id: this.instance.id || "",
                lifecycleRuleRequest: data,
            });
        }
        return new ReviewsApi(DEFAULT_CONFIG).reviewsLifecycleRulesCreate({
            lifecycleRuleRequest: data,
        });
    }

    protected serialize(): LifecycleRule | undefined {
        const ret = super.serialize();
        if (ret === undefined)
            return;
        if (this.selectedReviewerSelection === ReviewerSelection.Users) {
            ret.reviewers = (this.#reviewerUsersSelectRef.value?.value || []) as string[];
            ret.reviewerGroups = [];
            ret.minReviewers = 0;
        } else {
            ret.reviewerGroups = (this.#reviewerGroupsSelectRef.value?.value || []) as string[];
            ret.reviewers = [];
        }
        if (ret.objectId === "")
            ret.objectId = null;
        return ret;
    }

    private async loadObjects(query?: string): Promise<TargetObject[]> {
        switch (this.#selectedContentType) {
            case ContentTypeEnum.AuthentikCoreApplication:
                return (await new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
                    ordering: "name",
                    search: query,
                })).results;
            case ContentTypeEnum.AuthentikCoreGroup:
                return (await new CoreApi(DEFAULT_CONFIG).coreGroupsList({
                    ordering: "name",
                    search: query,
                })).results;
            case ContentTypeEnum.AuthentikRbacRole:
                return (await new RbacApi(DEFAULT_CONFIG).rbacRolesList({
                    ordering: "name",
                    search: query,
                })).results;
            default:
                return [];
        }

    }

    async #handleContentTypeChange(ev: Event): Promise<void> {
        this.#selectedContentType = (ev.target as HTMLSelectElement).value as ContentTypeEnum;
        await this.#targetSelectRef.value?.updateData();
    }

    #handleReviewerSelectionChange(ev: Event) {
        this.selectedReviewerSelection = (ev.target as HTMLInputElement).value as ReviewerSelection;
    }

    renderForm(): TemplateResult {
        return html`
            ${this.#renderTargetSelection()}
            <ak-form-element-horizontal label=${msg("Interval")} name="intervalMonths" required>
                <select class="pf-c-form-control">
                    ${[1, 2, 3, 4, 6, 8, 12, 18, 24].map(interval =>
                        html`
                            <option value=${interval}
                                    ?selected=${this.instance?.intervalMonths === interval}>
                                ${interval} ${interval === 1 ? msg("month") : msg("months")}
                            </option>`
                    )}
                </select>
            </ak-form-element-horizontal>
            <ak-number-input
                label=${msg("Grace period")}
                min=${1}
                required
                name="gracePeriodDays"
                value="${this.instance?.gracePeriodDays ?? 28}"
                help=${msg("Number of days before a review is considered overdue.")}
            ></ak-number-input>
            <ak-form-element-horizontal label=${msg("Reviewers")}>
                <div class="pf-c-form__group-control pf-m-stack">
                    <div class="ak-horizontal-radio-select">
                        <div class="pf-c-form__group-control pf-m-inline">
                            <div class="pf-c-radio">
                                <input type="radio" id="reviewer-selection-groups"
                                       name="reviewerSelection"
                                       class="pf-c-radio__input"
                                       value=${ReviewerSelection.Groups}
                                       ?checked=${this.selectedReviewerSelection === ReviewerSelection.Groups}
                                       @change=${this.#handleReviewerSelectionChange} />
                                <label for="reviewer-selection-groups"
                                       class="pf-c-radio__label">${msg("Anyone in chosen groups")}</label>
                            </div>
                            <div class="">
                                <input type="radio" id="reviewer-selection-users"
                                       name="reviewerSelection"
                                       class="pf-c-radio__input"
                                       ?checked=${this.selectedReviewerSelection === ReviewerSelection.Users}
                                       value=${ReviewerSelection.Users}
                                       @change=${this.#handleReviewerSelectionChange} />
                                <label for="reviewer-selection-users"
                                       class="pf-c-radio__label">${msg("Specific users")}</label>
                            </div>
                        </div>
                    </div>
                    <div class="">${this.#renderReviewerSelection()}</div>
                </div>
            </ak-form-element-horizontal>
            ${this.#renderTransportsSelection()}
        `;
    }

    #renderReviewerSelection(): TemplateResult {
        if (this.selectedReviewerSelection === ReviewerSelection.Groups)
            return html`
                ${this.#renderReviewerGroupsSelection()}
                <ak-number-input
                    label=${msg("Min reviewers")}
                    min=${1}
                    required
                    name="minReviewers"
                    value="${this.instance?.minReviewers ?? 1}"
                    help=${msg("Number of users from the selected reviewer groups that must approve the review.")}></ak-number-input>
            `;

        return html`${this.#renderReviewerUserSelection()}`;

    }

    #renderTargetSelection(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Object type")} required name="contentType">
                <select class="pf-c-form-control"
                        @change=${this.#handleContentTypeChange}
                >
                    <option value="" ?selected=${this.instance?.contentType === undefined}>
                        ---------
                    </option>
                    <option value=${ContentTypeEnum.AuthentikCoreApplication}
                            ?selected=${this.instance?.contentType === ContentTypeEnum.AuthentikCoreApplication}>
                        ${msg("Application")}
                    </option>
                    <option value=${ContentTypeEnum.AuthentikCoreGroup}
                            ?selected=${this.instance?.contentType === ContentTypeEnum.AuthentikCoreGroup}>
                        ${msg("Group")}
                    </option>
                    <option value=${ContentTypeEnum.AuthentikRbacRole}
                            ?selected=${this.instance?.contentType === ContentTypeEnum.AuthentikRbacRole}>
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
                    ${msg("When set, the rule will apply to the selected individual object. Otherwise, the rule applies to all objects of the selected type.")}
                </p>
            </ak-form-element-horizontal>`;
    }

    #renderReviewerGroupsSelection(): TemplateResult {
        return html`
            <ak-dual-select-provider
                ${ref(this.#reviewerGroupsSelectRef)}
                .provider=${this.#fetchGroups}
                .selected=${(this.instance?.reviewerGroupsObj ?? []).map(coreGroupPair)}
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
            ></ak-dual-select-provider>`;
    }

    #renderTransportsSelection(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Notification transports")} required
                                        name="notificationTransports">
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
