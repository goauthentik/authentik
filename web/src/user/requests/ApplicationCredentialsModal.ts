import "#elements/EmptyState";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { aki } from "#common/api/client";

import { AKModal } from "#elements/dialogs/ak-modal";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import { ApplicationCredentials, GrantRequest, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

/**
 * Shows the requester what to configure in the application their approved application request
 * created: client ID, client secret and the provider's URLs.
 */
@customElement("ak-application-credentials-modal")
export class ApplicationCredentialsModal extends AKModal {
    public static override styles: CSSResult[] = [...AKModal.styles, PFDescriptionList];

    @property({ attribute: false })
    public request: GrantRequest | null = null;

    @state()
    protected credentials: ApplicationCredentials | null = null;

    public override headline = msg("Application credentials", {
        id: "requests.application-credentials.header",
    });

    public override connectedCallback(): void {
        super.connectedCallback();

        if (!this.request) return;

        aki(RequestsApi)
            .requestsGrantRequestsCredentialsRetrieve({ uuid: this.request.uuid ?? "" })
            .then((credentials) => {
                this.credentials = credentials;
            })
            .catch(showAPIErrorMessage);
    }

    protected override render(): SlottedTemplateResult {
        const { credentials } = this;

        if (!credentials) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        const rows: [string, string | null | undefined][] = [
            [
                msg("Client ID", { id: "requests.application-credentials.client-id.label" }),
                credentials.clientId,
            ],
            [
                msg("Client secret", {
                    id: "requests.application-credentials.client-secret.label",
                }),
                credentials.clientSecret,
            ],
            [
                msg("Issuer", { id: "requests.application-credentials.issuer.label" }),
                credentials.urls.issuer,
            ],
            [
                msg("OpenID configuration URL", {
                    id: "requests.application-credentials.provider-info.label",
                }),
                credentials.urls.providerInfo,
            ],
            [
                msg("Authorize URL", { id: "requests.application-credentials.authorize.label" }),
                credentials.urls.authorize,
            ],
            [
                msg("Token URL", { id: "requests.application-credentials.token.label" }),
                credentials.urls.token,
            ],
            [
                msg("Userinfo URL", { id: "requests.application-credentials.user-info.label" }),
                credentials.urls.userInfo,
            ],
            [
                msg("Logout URL", { id: "requests.application-credentials.logout.label" }),
                credentials.urls.logout,
            ],
            [
                msg("JWKS URL", { id: "requests.application-credentials.jwks.label" }),
                credentials.urls.jwks,
            ],
        ];

        return html`<dl class="pf-c-description-list pf-m-horizontal">
            ${rows.map(([term, value]) =>
                value
                    ? html`<div class="pf-c-description-list__group">
                          <dt class="pf-c-description-list__term">
                              <span class="pf-c-description-list__text">${term}</span>
                          </dt>
                          <dd class="pf-c-description-list__description">
                              <div class="pf-c-description-list__text"><code>${value}</code></div>
                          </dd>
                      </div>`
                    : nothing,
            )}
        </dl>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-credentials-modal": ApplicationCredentialsModal;
    }
}
