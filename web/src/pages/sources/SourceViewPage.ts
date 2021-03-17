import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Source, SourcesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/EmptyState";

import "./LDAPSourceViewPage";
import "./OAuthSourceViewPage";
import "./SAMLSourceViewPage";

@customElement("ak-source-view")
export class SourceViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.sourceSlug = value.slug;
    }

    @property({ type: String })
    set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG).sourcesAllRead({
            slug: slug
        }).then((source) => {
            this.source = source;
        });
    }

    @property({ attribute: false })
    source?: Source;

    static get styles(): CSSResult[] {
        return [css`
            * {
                height: 100%;
            }
        `];
    }

    render(): TemplateResult {
        if (!this.source) {
            return html`<ak-empty-state ?loading=${true} ?fullHeight=${true}></ak-empty-state>`;
        }
        switch (this.source?.objectType) {
            case "ldap":
                return html`<ak-source-ldap-view sourceSlug=${this.source.slug}></ak-source-ldap-view>`;
            case "oauth":
                return html`<ak-source-oauth-view sourceSlug=${this.source.slug}></ak-source-oauth-view>`;
            case "saml":
                return html`<ak-source-saml-view sourceSlug=${this.source.slug}></ak-source-saml-view>`;
            default:
                return html`<p>Invalid source type ${this.source.objectType}</p>`;
        }
    }
}
