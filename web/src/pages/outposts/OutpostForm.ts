import { Outpost, OutpostsApi, OutpostTypeEnum, ProvidersApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import YAML from "yaml";

@customElement("ak-outpost-form")
export class OutpostForm extends Form<Outpost> {

    @property({attribute: false})
    outpost?: Outpost;

    getSuccessMessage(): string {
        if (this.outpost) {
            return t`Successfully updated outpost.`;
        } else {
            return t`Successfully created outpost.`;
        }
    }

    send = (data: Outpost): Promise<Outpost> => {
        if (this.outpost) {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsOutpostsUpdate({
                uuid: this.outpost.pk || "",
                data: data
            });
        } else {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsOutpostsCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.outpost?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Type`}
                ?required=${true}
                name="type">
                <select class="pf-c-form-control">
                    <option value=${OutpostTypeEnum.Proxy} ?selected=${this.outpost?.type === OutpostTypeEnum.Proxy}>${t`Proxy`}</option>
                    <option value=${OutpostTypeEnum.Ldap} ?selected=${this.outpost?.type === OutpostTypeEnum.Ldap}>${t`LDAP`}</option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Service connection`}
                name="serviceConnection">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.outpost?.serviceConnection === undefined}>---------</option>
                    ${until(new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsAllList({
                        ordering: "pk"
                    }).then(scs => {
                        return scs.results.map(sc => {
                            return html`<option value=${ifDefined(sc.pk)} ?selected=${this.outpost?.serviceConnection === sc.pk}>
                                ${sc.name} (${sc.verboseName})
                            </option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
                <p class="pf-c-form__helper-text">${t`Selecting a service-connection enables the management of the outpost by authentik.`}</p>
                <p class="pf-c-form__helper-text">
                    See <a target="_blank" href="https://goauthentik.io/docs/outposts/outposts">documentation</a>.
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Providers`}
                ?required=${true}
                name="providers">
                <select class="pf-c-form-control" multiple>
                    ${until(new ProvidersApi(DEFAULT_CONFIG).providersProxyList({
                        ordering: "pk"
                    }).then(providers => {
                        return providers.results.map(provider => {
                            const selected = Array.from(this.outpost?.providers || []).some(sp => {
                                return sp == provider.pk;
                            });
                            return html`<option value=${ifDefined(provider.pk)} ?selected=${selected}>${provider.verboseName} ${provider.name}</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                    ${until(new ProvidersApi(DEFAULT_CONFIG).providersLdapList({
                        ordering: "pk"
                    }).then(providers => {
                        return providers.results.map(provider => {
                            const selected = Array.from(this.outpost?.providers || []).some(sp => {
                                return sp == provider.pk;
                            });
                            return html`<option value=${ifDefined(provider.pk)} ?selected=${selected}>${provider.verboseName} ${provider.name}</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
                <p class="pf-c-form__helper-text">${t`Hold control/command to select multiple items.`}</p>
            </ak-form-element-horizontal>
            ${until(new OutpostsApi(DEFAULT_CONFIG).outpostsOutpostsDefaultSettings({}).then(config => {
                let fc = config.config;
                if (this.outpost) {
                    fc = this.outpost.config;
                }
                return html`<ak-form-element-horizontal
                    label=${t`Configuration`}
                    name="config">
                    <ak-codemirror mode="yaml" value="${YAML.stringify(fc)}"></ak-codemirror>
                    <p class="pf-c-form__helper-text">${t`Set custom attributes using YAML or JSON.`}</p>
                </ak-form-element-horizontal>`;
            }))}
        </form>`;
    }

}
