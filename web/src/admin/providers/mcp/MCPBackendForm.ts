import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/utils/TimeDeltaHelp";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import { Application, CoreApi, MCPBackend, ProvidersApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const applicationSource: SearchSelectSource<Application> = {
    fetchObjects: (query) =>
        aki(CoreApi)
            .coreApplicationsList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (application) => application.pk,
    labelOf: (application) => application.name,
    describe: (application) => html`${application.slug}`,
};

/**
 * Form for a backend MCP server of an MCP gateway.
 *
 * @element ak-provider-mcp-backend-form
 */
@customElement("ak-provider-mcp-backend-form")
export class MCPBackendForm extends ModelForm<MCPBackend, string> {
    public static override verboseName = msg("MCP Backend", { id: "mcp-backend.verbose-name" });
    public static override verboseNamePlural = msg("MCP Backends", {
        id: "mcp-backend.verbose-name-plural",
    });

    /** Gateway new backends are created for. */
    @property({ type: Number })
    public gateway?: number;

    protected loadInstance(pk: string): Promise<MCPBackend> {
        return aki(ProvidersApi).providersMcpBackendsRetrieve({ pbmUuid: pk });
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated backend.", { id: "mcp-backend.form.updated.success" })
            : msg("Successfully created backend.", { id: "mcp-backend.form.created.success" });
    }

    protected override send(data: MCPBackend): Promise<MCPBackend> {
        if (this.instance) {
            return aki(ProvidersApi).providersMcpBackendsPartialUpdate({
                pbmUuid: this.instance.pbmUuid,
                patchedMCPBackendRequest: data,
            });
        }
        data.gateway = this.gateway!;
        return aki(ProvidersApi).providersMcpBackendsCreate({ mCPBackendRequest: data });
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                name="name"
                label=${msg("Name", { id: "mcp-backend.form.name.label" })}
                value=${ifDefined(this.instance?.name)}
                required
            ></ak-text-input>
            <ak-text-input
                name="slug"
                label=${msg("Slug", { id: "mcp-backend.form.slug.label" })}
                value=${ifDefined(this.instance?.slug)}
                required
                input-hint="code"
                help=${msg("Tools of this backend are exposed as <slug>__<tool>.", {
                    id: "mcp-backend.form.slug.help",
                })}
            ></ak-text-input>
            <ak-text-input
                name="url"
                type="url"
                label=${msg("URL", { id: "mcp-backend.form.url.label" })}
                value=${ifDefined(this.instance?.url)}
                required
                input-hint="code"
                placeholder="https://mcp.example.com/mcp"
                help=${msg("Streamable HTTP endpoint of the MCP server.", {
                    id: "mcp-backend.form.url.help",
                })}
            ></ak-text-input>
            <ak-form-element-horizontal
                label=${msg("Token application", { id: "mcp-backend.form.token-application.label" })}
                name="tokenApplication"
            >
                ${AKSearchSelect({
                    name: "tokenApplication",
                    source: applicationSource,
                    placeholder: msg("Select an application...", {
                        id: "mcp-backend.form.token-application.placeholder",
                    }),
                    value: this.instance?.tokenApplication ?? undefined,
                    blankable: true,
                })}
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When set, every request to this backend carries a short-lived access token for the user, issued by this application's OAuth2/OpenID provider. Users must also have access to this application to use the backend's tools.",
                        { id: "mcp-backend.form.token-application.help" },
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-text-input
                name="tokenValidity"
                label=${msg("Token validity", { id: "mcp-backend.form.token-validity.label" })}
                value=${this.instance?.tokenValidity ?? "minutes=5"}
                required
                input-hint="code"
                .bighelp=${html`<ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            ></ak-text-input>
            <ak-form-element-horizontal
                label=${msg("Policy engine mode", { id: "mcp-backend.form.policy-engine-mode.label" })}
                required
                name="policyEngineMode"
            >
                <ak-radio .options=${policyEngineModes} .value=${this.instance?.policyEngineMode}>
                </ak-radio>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-mcp-backend-form": MCPBackendForm;
    }
}
