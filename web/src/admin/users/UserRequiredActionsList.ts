import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/SearchSelect/index";
import { aki } from "#common/api/client";
import { createPaginatedResponse } from "#common/api/responses";
import { AKRefreshEvent } from "#common/events";

import { SearchSelectChangeEvent } from "#elements/forms/SearchSelect/events";
import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { RenderFlowOption } from "#admin/flows/utils";

import {
    AuthenticationEnum,
    CoreApi,
    Flow,
    FlowDesignationEnum,
    FlowsApi,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

export const USER_ATTRIBUTE_REQUIRED_ACTIONS = "goauthentik.io/user/required-actions";

// Matches the server's rules for flows that can be required actions
const disallowedDesignations: FlowDesignationEnum[] = [
    FlowDesignationEnum.Authentication,
    FlowDesignationEnum.Invalidation,
];

const disallowedAuthentication: AuthenticationEnum[] = [
    AuthenticationEnum.RequireUnauthenticated,
    AuthenticationEnum.RequireOutpost,
    AuthenticationEnum.RequireRedirect,
    AuthenticationEnum.RequireToken,
];

function canBeRequiredAction(flow: Flow): boolean {
    return (
        !disallowedDesignations.includes(flow.designation) &&
        !(flow.authentication && disallowedAuthentication.includes(flow.authentication))
    );
}

const flowSource: SearchSelectSource<Flow> = {
    fetchObjects: (query) =>
        aki(FlowsApi)
            .flowsInstancesList(withQuery(query, { ordering: "slug" }))
            .then(({ results }) => results.filter(canBeRequiredAction)),
    keyOf: (flow) => flow.pk,
    labelOf: RenderFlowOption,
    describe: (flow) => flow.slug,
};

type RequiredActionRow = Pick<Flow, "name" | "slug">;

function toSlugs(value: unknown): string[] {
    const values = Array.isArray(value) ? value : [value];

    return values.filter((entry): entry is string => typeof entry === "string");
}

@customElement("ak-user-required-actions-list")
export class UserRequiredActionsList extends Table<RequiredActionRow> {
    public static override verboseName = msg("Required action", {
        id: "user-required-actions.object.label.one",
    });
    public static override verboseNamePlural = msg("Required actions", {
        id: "user-required-actions.object.label.other",
    });

    public static override styles: CSSResult[] = [
        ...super.styles,
        css`
            ak-search-select {
                display: inline-block;
                width: 24rem;
                max-width: 100%;
                flex-grow: 1;
            }
        `,
    ];

    #api = aki(CoreApi);

    @property({ attribute: false })
    public user?: User;

    @state()
    protected selectedFlow: Flow | null = null;

    protected override async apiEndpoint(): Promise<PaginatedResponse<RequiredActionRow>> {
        if (!this.user) {
            return createPaginatedResponse();
        }

        const user = await this.#api.coreUsersRetrieve({ id: this.user.pk });
        const slugs = toSlugs(user.attributes?.[USER_ATTRIBUTE_REQUIRED_ACTIONS]);

        const rows = await Promise.all(
            slugs.map(async (slug) => {
                const { results } = await aki(FlowsApi).flowsInstancesList({ slug });

                return results[0] ?? { name: slug, slug };
            }),
        );

        return createPaginatedResponse(rows);
    }

    protected override columns: TableColumn[] = [
        [msg("Flow", { id: "user-required-actions.column.flow.label" })],
        [msg("Slug", { id: "user-required-actions.column.slug.label" })],
        [msg("Actions", { id: "user-required-actions.column.actions.label" })],
    ];

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
        const actions = mutate(toSlugs(user.attributes?.[USER_ATTRIBUTE_REQUIRED_ACTIONS]));
        const attributes = { ...user.attributes };

        if (actions.length) {
            attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS] = actions;
        } else {
            delete attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS];
        }

        await this.#api.coreUsersPartialUpdate({
            id: user.pk,
            patchedUserRequest: { attributes },
        });

        this.dispatchEvent(new AKRefreshEvent());
    }

    protected addSelected = async () => {
        const slug = this.selectedFlow?.slug;

        if (!slug) {
            return;
        }

        await this.#patch((actions) => (actions.includes(slug) ? actions : [...actions, slug]));
        this.selectedFlow = null;
    };

    protected override renderToolbar(): SlottedTemplateResult {
        return html`
            <ak-search-select
                label=${msg("Flow", { id: "user-required-actions.column.flow.label" })}
                .source=${flowSource}
                .selectedObject=${this.selectedFlow}
                .value=${this.selectedFlow?.pk ?? ""}
                placeholder=${msg("Select a flow...", {
                    id: "user-required-actions.select.placeholder",
                })}
                blankable
                @ak-change=${(event: SearchSelectChangeEvent<Flow>) => {
                    event.stopPropagation();
                    this.selectedFlow = event.detail.value;
                }}
            ></ak-search-select>
            <ak-spinner-button
                class="pf-m-primary"
                .disabled=${!this.selectedFlow}
                .callAction=${this.addSelected}
            >
                ${msg("Add", { id: "user-required-actions.add.label" })}
            </ak-spinner-button>
            ${super.renderToolbar()}
        `;
    }

    protected override row(item: RequiredActionRow): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.slug}`,
            html`<ak-forms-delete-bulk
                object-label=${msg("Required action", {
                    id: "user-required-actions.object.label.one",
                })}
                .objects=${[item]}
                .delete=${() =>
                    this.#patch((actions) => actions.filter((entry) => entry !== item.slug))}
            >
                <button
                    slot="trigger"
                    class="pf-c-button pf-m-plain"
                    aria-label=${msg("Remove", { id: "user-required-actions.remove.label" })}
                >
                    <pf-tooltip
                        position="top"
                        content=${msg("Remove", { id: "user-required-actions.remove.label" })}
                    >
                        <i class="fas fa-trash" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-delete-bulk>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-required-actions-list": UserRequiredActionsList;
    }
}
