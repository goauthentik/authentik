import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { provide } from "@lit-labs/context";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { property } from "@lit/reactive-element/decorators/property.js";
import { LitElement, html } from "lit";

import {
    Application,
    LDAPProvider,
    OAuth2Provider,
    ProxyProvider,
    RadiusProvider,
    SAMLProvider,
    SCIMProvider,
} from "@goauthentik/api";

import applicationWizardContext from "./ak-application-wizard-context-name";

// my-context.ts

type OneOfProvider =
    | Partial<SCIMProvider>
    | Partial<SAMLProvider>
    | Partial<RadiusProvider>
    | Partial<ProxyProvider>
    | Partial<OAuth2Provider>
    | Partial<LDAPProvider>;

export type WizardState = {
    step: number;
    providerType: string;
    application: Partial<Application>;
    provider: OneOfProvider;
};

@customElement("ak-application-wizard-context")
export class AkApplicationWizardContext extends CustomListenerElement(LitElement) {
    /**
     * Providing a context at the root element
     */
    @provide({ context: applicationWizardContext })
    @property({ attribute: false })
    wizardState: WizardState = {
        step: 0,
        providerType: "",
        application: {},
        provider: {},
    };

    constructor() {
        super();
        this.handleUpdate = this.handleUpdate.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        this.addCustomListener("ak-wizard-update", this.handleUpdate);
    }

    disconnectedCallback() {
        this.removeCustomListener("ak-wizard-update", this.handleUpdate);
        super.disconnectedCallback();
    }

    handleUpdate(event: CustomEvent<WizardState>) {
        delete event.detail.target;
        this.wizardState = event.detail;
    }

    render() {
        return html`<slot></slot>`;
    }
}

export default AkApplicationWizardContext;
