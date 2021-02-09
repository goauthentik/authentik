import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { SpinnerSize } from "../../elements/Spinner";

import "./LDAPSourceViewPage";
import "./OAuthSourceViewPage";
import { Source } from "../../api/Sources";

@customElement("ak-source-view")
export class SourceViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.sourceSlug = value.slug;
    }

    @property({ type: String })
    set sourceSlug(slug: string) {
        Source.get(slug).then((app) => (this.source = app));
    }

    @property({ attribute: false })
    source?: Source;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
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
        switch (this.source?.object_type) {
            case "ldap":
                return html`<ak-source-ldap-view sourceSlug=${this.source.slug}></ak-source-ldap-view>`;
            case "oauth2":
                return html`<ak-source-oauth-view sourceSlug=${this.source.slug}></ak-source-oauth-view>`;
            // case "proxy":
            //     return html`<ak-provider-proxy-view providerID=${this.source.pk}></ak-provider-proxy-view>`;
            default:
                return html`<p>Invalid source type ${this.source.object_type}</p>`;
        }
    }
}
