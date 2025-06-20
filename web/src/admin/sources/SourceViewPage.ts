import "#admin/sources/kerberos/KerberosSourceViewPage";
import "#admin/sources/ldap/LDAPSourceViewPage";
import "#admin/sources/oauth/OAuthSourceViewPage";
import "#admin/sources/plex/PlexSourceViewPage";
import "#admin/sources/saml/SAMLSourceViewPage";
import "#admin/sources/scim/SCIMSourceViewPage";
import { DEFAULT_CONFIG } from "#common/api/config";
import "#components/ak-page-header";
import { AKElement } from "#elements/Base";
import "#elements/EmptyState";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Source, SourcesApi } from "@goauthentik/api";

@customElement("ak-source-view")
export class SourceViewPage extends AKElement {
    @property({ type: String })
    set sourceSlug(slug: string) {
        this._sourceSlug = slug;
    }

    get sourceSlug(): string {
        return this._sourceSlug || "";
    }

    _sourceSlug?: string;

    @property({ attribute: false })
    source?: Source | null;

    fetchSource(slug: string): void {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesAllRetrieve({
                slug: slug,
            })
            .then((source) => {
                this.source = source;
            })
            .catch((error) => {
                console.error(`Failed to fetch source with slug ${slug}:`, error);
                this.source = null as unknown as Source;
            });
    }

    updated(changedProperties: Map<string | number | symbol, unknown>): void {
        super.updated(changedProperties);
        if (changedProperties.has("_sourceSlug") && this._sourceSlug) {
            this.fetchSource(this._sourceSlug);
        }
    }

    renderSource(): TemplateResult {
        if (this.source === undefined) {
            return html`<ak-empty-state loading fullHeight></ak-empty-state>`;
        }

        if (this.source === null) {
            return html`<ak-empty-state 
                header=${msg("Source not found")}
                icon="fa fa-exclamation-triangle"
                fullHeight
            >
                <p>${msg("The requested source does not exist or you don't have permission to view it.")}</p>
            </ak-empty-state>`;
        }

        const handleFormSubmit = (e: CustomEvent) => {
            const source = e.detail as Source;
            ModelForm.handleIdentifierChange(this.sourceSlug || "", source.slug, "/core/sources/");
        };

        switch (this.source?.component) {
            case "ak-source-kerberos-form":
                return html`<ak-source-kerberos-view
                    sourceSlug=${this.source.slug}
                    @ak-form-successful-submit=${handleFormSubmit}
                ></ak-source-kerberos-view>`;
            case "ak-source-ldap-form":
                return html`<ak-source-ldap-view
                    sourceSlug=${this.source.slug}
                    @ak-form-successful-submit=${handleFormSubmit}
                ></ak-source-ldap-view>`;
            case "ak-source-oauth-form":
                return html`<ak-source-oauth-view
                    sourceSlug=${this.source.slug}
                    @ak-form-successful-submit=${handleFormSubmit}
                ></ak-source-oauth-view>`;
            case "ak-source-saml-form":
                return html`<ak-source-saml-view
                    sourceSlug=${this.source.slug}
                    @ak-form-successful-submit=${handleFormSubmit}
                ></ak-source-saml-view>`;
            case "ak-source-plex-form":
                return html`<ak-source-plex-view
                    sourceSlug=${this.source.slug}
                    @ak-form-successful-submit=${handleFormSubmit}
                ></ak-source-plex-view>`;
            case "ak-source-scim-form":
                return html`<ak-source-scim-view
                    sourceSlug=${this.source.slug}
                    @ak-form-successful-submit=${handleFormSubmit}
                ></ak-source-scim-view>`;
            default:
                return html`<p>Invalid source type ${this.source.component}</p>`;
        }
    }

    render(): TemplateResult {
        if (this.source === null) {
            return this.renderSource();
        }
        
        return html`<ak-page-header
                icon="pf-icon pf-icon-middleware"
                header=${ifDefined(this.source?.name)}
                description=${ifDefined(this.source?.verboseName)}
            >
            </ak-page-header>
            ${this.renderSource()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-view": SourceViewPage;
    }
}
