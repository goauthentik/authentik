import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SourcesApi, TypeCreate } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/ProxyForm";
import "../../elements/wizard/FormWizardPage";
import "../../elements/wizard/Wizard";
import { WizardPage } from "../../elements/wizard/WizardPage";
import "./ldap/LDAPSourceForm";
import "./oauth/OAuthSourceForm";
import "./plex/PlexSourceForm";
import "./saml/SAMLSourceForm";

@customElement("ak-source-wizard-initial")
export class InitialSourceWizardPage extends WizardPage {
    @property({ attribute: false })
    sourceTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, AKGlobal, PFRadio];
    }

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.sourceTypes.map((type) => {
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${`${type.component}-${type.modelName}`}
                        @change=${() => {
                            this.host.setSteps(
                                "initial",
                                `type-${type.component}-${type.modelName}`,
                            );
                            this._isValid = true;
                        }}
                    />
                    <label class="pf-c-radio__label" for=${`${type.component}-${type.modelName}`}
                        >${type.name}</label
                    >
                    <span class="pf-c-radio__description">${type.description}</span>
                </div>`;
            })}
        </form>`;
    }
}

@customElement("ak-source-wizard")
export class SourceWizard extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    @property({ attribute: false })
    sourceTypes: TypeCreate[] = [];

    firstUpdated(): void {
        new SourcesApi(DEFAULT_CONFIG).sourcesAllTypesList().then((types) => {
            this.sourceTypes = types;
        });
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${t`New source`}
                description=${t`Create a new source.`}
            >
                <ak-source-wizard-initial
                    slot="initial"
                    .sidebarLabel=${() => t`Select type`}
                    .sourceTypes=${this.sourceTypes}
                >
                </ak-source-wizard-initial>
                ${this.sourceTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            .sidebarLabel=${() => t`Create ${type.name}`}
                        >
                            <ak-proxy-form
                                .args=${{
                                    modelName: type.modelName,
                                }}
                                type=${type.component}
                            ></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-wizard>
        `;
    }
}
