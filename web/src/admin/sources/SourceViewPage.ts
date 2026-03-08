import "#admin/sources/kerberos/KerberosSourceViewPage";
import "#admin/sources/ldap/LDAPSourceViewPage";
import "#admin/sources/oauth/OAuthSourceViewPage";
import "#admin/sources/plex/PlexSourceViewPage";
import "#admin/sources/saml/SAMLSourceViewPage";
import "#admin/sources/scim/SCIMSourceViewPage";
import "#admin/sources/telegram/TelegramSourceViewPage";
import "#elements/EmptyState";
import "#elements/buttons/SpinnerButton/ak-spinner-button";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { setPageDetails } from "#components/ak-page-navbar";

import { Source, SourcesApi } from "@goauthentik/api";

import { html, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

function resolveSourceViewComponentName(component: string) {
    switch (component) {
        case "ak-source-kerberos-form":
            return "ak-source-kerberos-view";
        case "ak-source-ldap-form":
            return "ak-source-ldap-view";
        case "ak-source-oauth-form":
            return "ak-source-oauth-view";
        case "ak-source-saml-form":
            return "ak-source-saml-view";
        case "ak-source-plex-form":
            return "ak-source-plex-view";
        case "ak-source-scim-form":
            return "ak-source-scim-view";
        case "ak-source-telegram-form":
            return "ak-source-telegram-view";
        default:
            return null;
    }
}

@customElement("ak-source-view")
export class SourceViewPage extends AKElement {
    @property({ type: String, attribute: "source-slug" })
    public get sourceSlug() {
        return this.source?.slug || "";
    }

    public set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG).sourcesAllRetrieve({ slug }).then((source) => {
            this.source = source;
        });
    }

    @property({ attribute: false })
    source?: Source;

    render(): SlottedTemplateResult {
        if (!this.source) {
            return html`<ak-empty-state loading full-height></ak-empty-state>`;
        }

        const sourceViewComponentName = resolveSourceViewComponentName(this.source.component);

        if (!sourceViewComponentName) {
            return html`<p>Invalid source type ${this.source.component}</p>`;
        }

        return StrictUnsafe(sourceViewComponentName, {
            sourceSlug: this.source.slug,
        });
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

export default SourceViewPage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-view": SourceViewPage;
    }
}
