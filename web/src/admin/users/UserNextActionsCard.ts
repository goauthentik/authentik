import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";
import { AKRefreshEvent } from "#common/events";

import { AKElement } from "#elements/Base";
import type { SearchSelectBase } from "#elements/forms/SearchSelect/SearchSelect";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";

import { RenderFlowOption } from "#admin/flows/utils";
import Styles from "#admin/users/UserNextActionsCard.css";

import { CoreApi, Flow, FlowDesignationEnum, FlowsApi, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";

export const USER_ATTRIBUTE_NEXT_ACTIONS = "goauthentik.io/user/next-actions";

const disallowedDesignations: FlowDesignationEnum[] = [
    FlowDesignationEnum.Authentication,
    FlowDesignationEnum.Invalidation,
];

/**
 * Card on the user overview page to manage the flows a user must complete
 * on their next login.
 */
@customElement("ak-user-next-actions-card")
export class UserNextActionsCard extends AKElement {
    #api = aki(CoreApi);

    @property({ attribute: false })
    public user?: User;

    @state()
    protected selectedFlow: Flow | null = null;

    static styles = [PFCard, PFContent, PFButton, PFDataList, Styles];

    protected get actions(): string[] {
        const value = this.user?.attributes?.[USER_ATTRIBUTE_NEXT_ACTIONS];

        if (typeof value === "string") {
            return [value];
        }

        if (Array.isArray(value)) {
            return value.filter((entry): entry is string => typeof entry === "string");
        }

        return [];
    }

    protected fetchFlows = (query?: string): Promise<Flow[]> =>
        aki(FlowsApi)
            .flowsInstancesList({
                ordering: "slug",
                ...(query ? { search: query } : {}),
            })
            .then((flows) =>
                flows.results.filter(
                    (flow) =>
                        !flow.designation || !disallowedDesignations.includes(flow.designation),
                ),
            );

    #save(actions: string[]): Promise<boolean> {
        if (!this.user) {
            return Promise.resolve(false);
        }

        const attributes = { ...this.user.attributes };

        if (actions.length) {
            attributes[USER_ATTRIBUTE_NEXT_ACTIONS] = actions;
        } else {
            delete attributes[USER_ATTRIBUTE_NEXT_ACTIONS];
        }

        return this.#api
            .coreUsersPartialUpdate({
                id: this.user.pk,
                patchedUserRequest: { attributes },
            })
            .then(() => {
                this.dispatchEvent(new AKRefreshEvent());
                return true;
            })
            .catch((error) => {
                showAPIErrorMessage(error);
                return false;
            });
    }

    protected addSelected = () => {
        const slug = this.selectedFlow?.slug;

        if (!slug || this.actions.includes(slug)) {
            return;
        }

        this.#save([...this.actions, slug]).then((saved) => {
            if (!saved) {
                return;
            }

            const search =
                this.renderRoot.querySelector<SearchSelectBase<Flow>>("ak-search-select");

            if (search) {
                search.selectedObject = null;
            }

            this.selectedFlow = null;
        });
    };

    protected removeAction = (slug: string) => {
        this.#save(this.actions.filter((entry) => entry !== slug));
    };

    protected override render() {
        if (!this.user) {
            return nothing;
        }

        const actions = this.actions;

        return html`
            <div class="pf-c-card__title">
                ${msg("Next actions on login", { id: "user-next-actions.card.title" })}
            </div>
            <div class="pf-c-card__body">
                ${actions.length
                    ? html`<ul class="pf-c-data-list pf-m-compact" role="list">
                          ${actions.map(
                              (slug) => html`
                                  <li class="pf-c-data-list__item">
                                      <div class="pf-c-data-list__item-row">
                                          <div
                                              class="pf-c-data-list__item-content ak-next-action-slug"
                                          >
                                              ${slug}
                                          </div>
                                          <div class="pf-c-data-list__item-action">
                                              <button
                                                  class="pf-c-button pf-m-plain"
                                                  aria-label=${msg("Remove action", {
                                                      id: "user-next-actions.remove.aria-label",
                                                  })}
                                                  @click=${() => this.removeAction(slug)}
                                              >
                                                  <i class="fas fa-times" aria-hidden="true"></i>
                                              </button>
                                          </div>
                                      </div>
                                  </li>
                              `,
                          )}
                      </ul>`
                    : html`<p class="ak-next-actions-empty">
                          ${msg("No actions pending.", {
                              id: "user-next-actions.empty.description",
                          })}
                      </p>`}
            </div>
            <div class="pf-c-card__footer">
                <ak-search-select
                    .fetchObjects=${this.fetchFlows}
                    .renderElement=${RenderFlowOption}
                    .renderDescription=${(flow: Flow) => html`${flow.slug}`}
                    .value=${(flow: Flow | null) => String(flow?.pk ?? "")}
                    placeholder=${msg("Select a flow...", {
                        id: "user-next-actions.select.placeholder",
                    })}
                    blankable
                    @ak-change=${(event: CustomEvent<{ value: Flow | null }>) => {
                        event.stopPropagation();
                        this.selectedFlow = event.detail.value;
                    }}
                >
                </ak-search-select>
                <button
                    class="pf-c-button pf-m-secondary"
                    ?disabled=${!this.selectedFlow}
                    @click=${this.addSelected}
                >
                    ${msg("Add", { id: "user-next-actions.add.label" })}
                </button>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-next-actions-card": UserNextActionsCard;
    }
}
