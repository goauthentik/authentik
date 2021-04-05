import { SourcesApi } from "authentik-api";
import { customElement, html, LitElement, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import "./LDAPSyncStatusCard";
import { t } from "@lingui/macro";
import { DEFAULT_CONFIG } from "../../../api/Config";

@customElement("ak-admin-status-card-ldap-sync-container")
export class LDAPSyncStatusCardContainer extends LitElement {

    createRenderRoot(): Element | ShadowRoot {
        return this;
    }

    render(): TemplateResult {
        return html`
            ${until(new SourcesApi(DEFAULT_CONFIG).sourcesLdapList({}).then(sources => {
                return sources.results.map(source => {
                    return html`<ak-admin-status-card-ldap-sync
                        class="pf-l-gallery__item pf-m-4-col"
                        icon="fa fa-sync-alt"
                        header=${t`LDAP Sync status ${source.name}`}
                        slug=${source.slug}>
                    </ak-admin-status-card-ldap-sync>`;
                });
            }))}
        `;
    }

}
