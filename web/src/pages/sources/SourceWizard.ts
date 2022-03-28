import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";

import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";

import { FormWizardStep } from "../../elements/wizard/FormWizardStep";
import { Wizard } from "../../elements/wizard/Wizard";
import { WizardStep } from "../../elements/wizard/WizardStep";
import "./ldap/LDAPSourceForm";
import "./oauth/OAuthSourceForm";
import "./plex/PlexSourceForm";
import "./saml/SAMLSourceForm";

export class SourceInitialStep extends WizardStep {
    selected = false;

    isValid(): boolean {
        return this.selected;
    }

    renderNavList(): TemplateResult {
        return html`${t`Select type`}`;
    }

    render(): TemplateResult {
        return html`
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="oauth"
                    @change=${() => {
                        this.host.setSteps(this, new SourceOAuthDetailStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="oauth">${t`OAuth/OIDC`}</label>
                <span class="pf-c-radio__description"
                    >${t`Add a Source which supports SAML 2.0, by importing it's metadata.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="saml"
                    @change=${() => {
                        this.host.setSteps(this, new SourceSAMLDetailStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="saml">${t`SAML`}</label>
                <span class="pf-c-radio__description"
                    >${t`Authenticate using an external SAML Identity Provider.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="plex"
                    @change=${() => {
                        this.host.setSteps(this, new SourcePlexDetailStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="plex">${t`Plex`}</label>
                <span class="pf-c-radio__description"
                    >${t`Authenticate against plex.tv.`}</span
                >
            </div>`;
    }
}

class SourceOAuthDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`OAuth details`}`;
    }
    render(): TemplateResult {
        return html`<ak-source-oauth-form></ak-source-oauth-form>`;
    }
}

class SourceSAMLDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`SAML details`}`;
    }
    render(): TemplateResult {
        return html`<ak-source-saml-form></ak-source-saml-form>`;
    }
}

class SourceLDAPDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`LDAP details`}`;
    }
    render(): TemplateResult {
        return html`<ak-source-ldap-form></ak-source-ldap-form>`;
    }
}

class SourcePlexDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Plex details`}`;
    }
    render(): TemplateResult {
        return html`<ak-source-plex-form></ak-source-plex-form>`;
    }
}

@customElement("ak-source-wizard")
export class SourceWizard extends Wizard {
    header = t`New Source`;
    description = t`Create a new Source.`;

    steps = [new SourceInitialStep()];

    static get styles(): CSSResult[] {
        return super.styles.concat(PFRadio);
    }
}
