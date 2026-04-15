import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";

import { Application, CoreApi, CoreApplicationsListRequest, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

const USER_ATTRIBUTE_AGENT_OWNER_PK = "goauthentik.io/agent/owner-pk";

@customElement("ak-agent-add-application-form")
export class AgentAddApplicationForm extends Form<{ app: string }> {
    public override headline = msg("Add Application");
    public override submitLabel = msg("Add");

    @property({ attribute: false })
    public agent: User | null = null;

    public override getSuccessMessage(): string {
        return msg("Successfully added application.");
    }

    async send(data: { app: string }): Promise<{ app: string }> {
        if (!this.agent) throw new Error("Agent not set");
        await new CoreApi(DEFAULT_CONFIG).coreUsersAgentAllowedAppPartialUpdate({
            id: this.agent.pk,
            patchedUserAgentAllowedAppRequest: { app: data.app, action: "add" },
        });
        return data;
    }

    protected override renderForm(): TemplateResult {
        const ownerPk = this.agent?.attributes?.[USER_ATTRIBUTE_AGENT_OWNER_PK];

        return html`<ak-form-element-horizontal label=${msg("Application")} required name="app">
            <ak-search-select
                placeholder=${msg("Select an application...")}
                .fetchObjects=${async (query?: string): Promise<Application[]> => {
                    const args: CoreApplicationsListRequest = {
                        ordering: "name",
                        pageSize: 20,
                        forUser: ownerPk ? Number(ownerPk) : undefined,
                    };
                    if (query) {
                        args.search = query;
                    }
                    const result = await new CoreApi(DEFAULT_CONFIG).coreApplicationsList(args);
                    return result.results;
                }}
                .renderElement=${(app: Application): string => {
                    return app.name;
                }}
                .value=${(app: Application | undefined): string | undefined => {
                    return app?.pk;
                }}
                .renderDescription=${(app: Application): TemplateResult => {
                    return html`${app.group || msg("No group")}`;
                }}
            >
            </ak-search-select>
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-agent-add-application-form": AgentAddApplicationForm;
    }
}
