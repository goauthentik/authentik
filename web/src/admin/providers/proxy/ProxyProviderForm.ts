import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-flow-search";

import { renderForm, SetMode, SetShowHttpBasic } from "./ProxyProviderFormForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import { ProvidersApi, ProxyMode, ProxyProvider } from "@goauthentik/api";

import { CSSResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

@customElement("ak-provider-proxy-form")
export class ProxyProviderFormPage extends BaseProviderForm<ProxyProvider> {
    static styles: CSSResult[] = [...super.styles, PFContent, PFList, PFSpacing];

    async loadInstance(pk: number): Promise<ProxyProvider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersProxyRetrieve({
            id: pk,
        });
        this.showHttpBasic = provider.basicAuthEnabled ?? true;
        this.mode = provider.mode ?? ProxyMode.Proxy;
        return provider;
    }

    @state()
    showHttpBasic = true;

    @state()
    mode: ProxyMode = ProxyMode.Proxy;

    reset(): void {
        super.reset();
        this.showHttpBasic = true;
        this.mode = ProxyMode.Proxy;
    }

    async send(data: ProxyProvider): Promise<ProxyProvider> {
        data.mode = this.mode;
        if (this.mode !== ProxyMode.ForwardDomain) {
            data.cookieDomain = "";
        }
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersProxyUpdate({
                id: this.instance.pk,
                proxyProviderRequest: data,
            });
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersProxyCreate({
            proxyProviderRequest: data,
        });
    }

    renderForm() {
        const onSetMode: SetMode = (ev) => {
            this.mode = ev.detail.value;
        };

        const onSetShowHttpBasic: SetShowHttpBasic = (ev: Event) => {
            const el = ev.target as HTMLInputElement;
            this.showHttpBasic = el.checked;
        };

        return renderForm({
            provider: this.instance ?? {},
            args: {
                mode: this.mode,
                onSetMode,
                showHttpBasic: this.showHttpBasic,
                onSetShowHttpBasic,
            },
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-proxy-form": ProxyProviderFormPage;
    }
}
