import "#components/ak-text-input";
import "#elements/ak-array-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import "#admin/agents/AgentIDJAGResource";
import { aki } from "#common/api/client";

import { DataProvider, DualSelectPair, DualSelectPairSource } from "#elements/ak-dual-select/types";
import { ModelForm } from "#elements/forms/ModelForm";

import { Agent, AgentsApi, Application, CoreApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

const applicationToSelect = (app: Application): DualSelectPair<Application> => [
    app.pk,
    app.name,
    app.name,
    app,
];

const applicationsProvider: DataProvider = async (page = 1, search = "") => {
    const apps = await aki(CoreApi).coreApplicationsList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: apps.pagination,
        options: apps.results.map(applicationToSelect),
    };
};

function applicationsSelector(selected: string[] | undefined): DualSelectPairSource<Application> {
    return async () => {
        const apps = await Promise.allSettled(
            (selected ?? []).map((pbmUuid) => aki(CoreApi).coreApplicationsList({ pbmUuid })),
        );

        return apps
            .filter((s) => s.status === "fulfilled")
            .flatMap((s) => s.value.results)
            .map(applicationToSelect);
    };
}

/** Applications and ID-JAG settings of a system agent */
@customElement("ak-agent-id-jag-form")
export class AgentIDJAGForm extends ModelForm<Agent, number> {
    public static override verboseName = msg("Agent");
    public static override verboseNamePlural = msg("Agents");

    static styles = [
        ...super.styles,
        css`
            ak-array-input {
                width: 100%;
            }
        `,
    ];

    protected loadInstance(pk: number): Promise<Agent> {
        return aki(AgentsApi).agentsAgentsRetrieve({ id: pk });
    }

    getSuccessMessage(): string {
        return msg("Successfully updated agent.", { id: "agent.id-jag.form.success" });
    }

    protected async send(data: Agent): Promise<Agent> {
        return aki(AgentsApi).agentsAgentsPartialUpdate({
            id: this.instance!.pk,
            patchedAgentRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal
                label=${msg("Applications", { id: "agent.applications.label" })}
                name="applications"
            >
                <ak-dual-select-dynamic-selected
                    .provider=${applicationsProvider}
                    .selector=${applicationsSelector(this.instance?.applications)}
                    available-label=${msg("Available Applications", {
                        id: "agent.applications.available.label",
                    })}
                    selected-label=${msg("Selected Applications", {
                        id: "agent.applications.selected.label",
                    })}
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Applications that may use this agent. Their providers can mint ID-JAGs for the authorization server below via token exchange.",
                        { id: "agent.applications.description" },
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-text-input
                name="idJagAudience"
                label=${msg("ID-JAG audience", { id: "agent.id-jag.audience.label" })}
                value=${this.instance?.idJagAudience ?? ""}
                input-hint="code"
                help=${msg(
                    "Issuer of the authorization server ID-JAGs are minted for, exactly as its metadata names it.",
                    { id: "agent.id-jag.audience.description" },
                )}
            ></ak-text-input>
            <ak-text-input
                name="idJagClientId"
                label=${msg("ID-JAG client ID", { id: "agent.id-jag.client-id.label" })}
                value=${this.instance?.idJagClientId ?? ""}
                input-hint="code"
                help=${msg("Identifier of the client at that authorization server.", {
                    id: "agent.id-jag.client-id.description",
                })}
            ></ak-text-input>
            <ak-form-element-horizontal
                label=${msg("ID-JAG resources", { id: "agent.id-jag.resources.label" })}
                name="idJagResources"
            >
                <ak-array-input
                    .items=${this.instance?.idJagResources ?? []}
                    .newItem=${() => ""}
                    .row=${(resource: string) =>
                        html`<ak-agent-id-jag-resource
                            name="id-jag-resource"
                            style="width: 100%"
                            .resource=${resource}
                        ></ak-agent-id-jag-resource>`}
                ></ak-array-input>
                <p class="pf-c-form__helper-text">
                    ${msg("Resources an ID-JAG may be requested for at that server.", {
                        id: "agent.id-jag.resources.description",
                    })}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-agent-id-jag-form": AgentIDJAGForm;
    }
}
