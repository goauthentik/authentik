import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

import ApplicationWizardPageBase from "./ApplicationWizardPageBase";
import "./ldap/ak-application-wizard-authentication-by-ldap";
import "./oauth/ak-application-wizard-authentication-by-oauth";
import "./proxy/ak-application-wizard-authentication-for-reverse-proxy";
import "./proxy/ak-application-wizard-authentication-for-single-forward-proxy";

// prettier-ignore
const handlers = new Map<string, () => TemplateResult>([
    ["ldapprovider`", () => html`<ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>`],
    ["oauth2provider", () => html`<ak-application-wizard-authentication-by-oauth></ak-application-wizard-authentication-by-oauth>`],
    ["proxyprovider-proxy", () => html`<ak-application-wizard-authentication-for-reverse-proxy></ak-application-wizard-authentication-for-reverse-proxy>`],
    ["proxyprovider-forwardsingle", () => html`<ak-application-wizard-authentication-for-single-forward-proxy></ak-application-wizard-authentication-for-single-forward-proxy>`],
    ["radiusprovider", () => html`<p>Under construction</p>`],
    ["samlprovider", () => html`<p>Under construction</p>`],
    ["scimprovider", () => html`<p>Under construction</p>`],
]);

@customElement("ak-application-wizard-authentication-method")
export class ApplicationWizardApplicationDetails extends ApplicationWizardPageBase {
    render() {
        const handler = handlers.get(this.wizard.providerType);
        if (!handler) {
            throw new Error(
                "Unrecognized authentication method in ak-application-wizard-authentication-method",
            );
        }
        return handler();
    }
}

export default ApplicationWizardApplicationDetails;
