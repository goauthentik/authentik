import "#components/ak-text-input";
import { aki } from "#common/api/client";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import { MCPGatewayProvider, ProvidersApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * Form for an MCP gateway provider. Backends are managed on the provider's view page.
 *
 * @element ak-provider-mcp-gateway-form
 */
@customElement("ak-provider-mcp-gateway-form")
export class MCPGatewayProviderForm extends BaseProviderForm<MCPGatewayProvider> {
    protected endpoints = {
        load: (id: number) => aki(ProvidersApi).providersMcpRetrieve({ id }),
        create: (mCPGatewayProviderRequest: MCPGatewayProvider) =>
            aki(ProvidersApi).providersMcpCreate({ mCPGatewayProviderRequest }),
        update: (id: number, mCPGatewayProviderRequest: MCPGatewayProvider) =>
            aki(ProvidersApi).providersMcpUpdate({ id, mCPGatewayProviderRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
            name="name"
            label=${msg("Provider Name", { id: "mcp-gateway.form.name.label" })}
            placeholder=${msg("Type a provider name...", {
                id: "mcp-gateway.form.name.placeholder",
            })}
            spellcheck="false"
            value=${ifDefined(this.instance?.name)}
            required
            help=${msg(
                "Add this provider as a backchannel provider to an application with an OAuth2/OpenID provider. MCP clients sign in through that provider.",
                { id: "mcp-gateway.form.name.help" },
            )}
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-mcp-gateway-form": MCPGatewayProviderForm;
    }
}
