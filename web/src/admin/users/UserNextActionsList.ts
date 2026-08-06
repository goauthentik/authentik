import "#elements/forms/DeleteBulkForm";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";
import { createPaginatedResponse } from "#common/api/responses";
import { AKRefreshEvent } from "#common/events";

import type { SearchSelectBase } from "#elements/forms/SearchSelect/SearchSelect";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { RenderFlowOption } from "#admin/flows/utils";

import { CoreApi, Flow, FlowDesignationEnum, FlowsApi, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

export const USER_ATTRIBUTE_NEXT_ACTIONS = "goauthentik.io/user/next-actions";

const disallowedDesignations: FlowDesignationEnum[] = [
    FlowDesignationEnum.Authentication,
    FlowDesignationEnum.Invalidation,
];

interface NextActionRow {
    name: string;
    slug: string;
    flow: Flow | null;
}

function toSlugs(value: unknown): string[] {
    if (typeof value === "string") {
        return [value];
    }

    if (Array.isArray(value)) {
        return value.filter((entry): entry is string => typeof entry === "string");
    }

    return [];
}

/**
 * Table on the user overview page listing the flows a user must complete on
 * their next login.
 */
@customElement("ak-user-next-actions-list")
export class UserNextActionsList extends Table<NextActionRow> {
    public static override verboseName = msg("Next action");
    public static override verboseNamePlural = msg("Next actions");

    public static override styles: CSSResult[] = [
        ...super.styles,
        css`
            ak-search-select {
                display: inline-block;
                min-width: 24rem;
                max-width: 32rem;
                flex-grow: 1;
            }
        `,
    ];

    #api = aki(CoreApi);

    @property({ attribute: false })
    public user?: User;

    @state()
    protected selectedFlow: Flow | null = null;

    protected override async apiEndpoint(): Promise<PaginatedResponse<NextActionRow>> {
        const slugs = toSlugs(this.user?.attributes?.[USER_ATTRIBUTE_NEXT_ACTIONS]);
        const flows = slugs.length
            ? (await aki(FlowsApi).flowsInstancesList({ ordering: "slug" })).results
            : [];

        return createPaginatedResponse(
            slugs.map((slug) => ({
                name: slug,
                slug,
                flow: flows.find((flow) => flow.slug === slug) ?? null,
            })),
        );
    }

    protected override columns: TableColumn[] = [[msg("Flow")], [msg("Slug")], [msg("Actions")]];

    protected override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        if (changed.has("user") && this.user) {
            this.fetch();
        }
    }

    async #patch(mutate: (actions: string[]) => string[]): Promise<void> {
        if (!this.user) {
            return;
        }

        // Re-fetch the user so consecutive changes don't work on stale attributes
        const user = await this.#api.coreUsersRetrieve({ id: this.user.pk });
        const actions = mutate(toSlugs(user.attributes?.[USER_ATTRIBUTE_NEXT_ACTIONS]));
        const attributes = { ...user.attributes };

        if (actions.length) {
            attributes[USER_ATTRIBUTE_NEXT_ACTIONS] = actions;
        } else {
            delete attributes[USER_ATTRIBUTE_NEXT_ACTIONS];
        }

        await this.#api.coreUsersPartialUpdate({
            id: user.pk,
            patchedUserRequest: { attributes },
        });
        this.dispatchEvent(new AKRefreshEvent());
    }

    protected addSelected = () => {
        const slug = this.selectedFlow?.slug;

        if (!slug) {
            return;
        }

        this.#patch((actions) => (actions.includes(slug) ? actions : [...actions, slug]))
            .then(() => {
                const search =
                    this.renderRoot.querySelector<SearchSelectBase<Flow>>("ak-search-select");

                if (search) {
                    search.selectedObject = null;
                }

                this.selectedFlow = null;
            })
            .catch(showAPIErrorMessage);
    };

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

    protected override renderToolbar(): SlottedTemplateResult {
        return html`
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
                class="pf-c-button pf-m-primary"
                ?disabled=${!this.selectedFlow}
                @click=${this.addSelected}
            >
                ${msg("Add", { id: "user-next-actions.add.label" })}
            </button>
            ${super.renderToolbar()}
        `;
    }

    protected override row(item: NextActionRow): SlottedTemplateResult[] {
        return [
            html`${item.flow?.name ?? item.slug}`,
            html`${item.slug}`,
            html`<ak-forms-delete-bulk
                objectLabel=${msg("Next action", { id: "user-next-actions.object.label" })}
                .objects=${[item]}
                .delete=${() =>
                    this.#patch((actions) => actions.filter((entry) => entry !== item.slug))}
            >
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Remove")}>
                        <i class="fas fa-trash" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-delete-bulk>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-next-actions-list": UserNextActionsList;
    }
}
