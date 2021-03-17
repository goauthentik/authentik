import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Source, SourcesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { SpinnerSize } from "../../elements/Spinner";

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
        return [PFPage, PFGallery, PFContent].concat(css`
            * {
                height: 100%;
            }
        `);
    }

    render(): TemplateResult {
        if (!this.source) {
            return html`<div class="pf-c-empty-state pf-m-full-height">
                <div class="pf-c-empty-state__content">
                    <div class="pf-l-bullseye">
                        <div class="pf-l-bullseye__item">
                            <ak-spinner size="${SpinnerSize.XLarge}"></ak-spinner>
                        </div>
                    </div>
                </div>
            </div>`;
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
