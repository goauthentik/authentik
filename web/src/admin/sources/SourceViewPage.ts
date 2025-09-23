import "#admin/sources/kerberos/KerberosSourceViewPage";
import "#admin/sources/ldap/LDAPSourceViewPage";
import "#admin/sources/oauth/OAuthSourceViewPage";
import "#admin/sources/plex/PlexSourceViewPage";
import "#admin/sources/saml/SAMLSourceViewPage";
import "#admin/sources/scim/SCIMSourceViewPage";
import "#elements/EmptyState";
import "#elements/buttons/SpinnerButton/ak-spinner-button";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { Source, SourcesApi } from "@goauthentik/api";

import { html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-view")
export class SourceViewPage extends AKElement {
    @property({ type: String })
    set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesAllRetrieve({
                slug: slug,
            })
            .then((source) => {
                this.source = source;
            });
    }

    @property({ attribute: false })
    source?: Source;

    render(): TemplateResult {
        if (!this.source) {
            return html`<ak-empty-state loading full-height></ak-empty-state>`;
        }
        switch (this.source?.component) {
            case "ak-source-kerberos-form":
                return html`<ak-source-kerberos-view
                    sourceSlug=${this.source.slug}
                ></ak-source-kerberos-view>`;
            case "ak-source-ldap-form":
                return html`<ak-source-ldap-view
                    sourceSlug=${this.source.slug}
                ></ak-source-ldap-view>`;
            case "ak-source-oauth-form":
                return html`<ak-source-oauth-view
                    sourceSlug=${this.source.slug}
                ></ak-source-oauth-view>`;
            case "ak-source-saml-form":
                return html`<ak-source-saml-view
                    sourceSlug=${this.source.slug}
                ></ak-source-saml-view>`;
            case "ak-source-plex-form":
                return html`<ak-source-plex-view
                    sourceSlug=${this.source.slug}
                ></ak-source-plex-view>`;
            case "ak-source-scim-form":
                return html`<ak-source-scim-view
                    sourceSlug=${this.source.slug}
                ></ak-source-scim-view>`;
            default:
                return html`<p>Invalid source type ${this.source.component}</p>`;
        }
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-middleware",
            header: this.source?.name,
            description: this.source?.verboseName,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-view": SourceViewPage;
    }
}
