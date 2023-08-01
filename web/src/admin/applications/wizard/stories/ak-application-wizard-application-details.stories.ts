import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-application-wizard-application-details";
import AkApplicationWizardApplicationDetails from "../ak-application-wizard-application-details";
import "../ak-application-wizard-authentication-method-choice";
import "../ak-application-wizard-context";
import "./ak-application-context-display-for-test";

// prettier-ignore
const providerTypes = [
    ["LDAP Provider", "ldapprovider", 
     "Allow applications to authenticate against authentik's users using LDAP.", 
    ], 
    ["OAuth2/OpenID Provider", "oauth2provider", 
     "OAuth2 Provider for generic OAuth and OpenID Connect Applications.", 
    ], 
    ["Proxy Provider", "proxyprovider", 
     "Protect applications that don't support any of the other\n    Protocols by using a Reverse-Proxy.", 
    ], 
    ["Radius Provider", "radiusprovider", 
     "Allow applications to authenticate against authentik's users using Radius.", 
    ], 
    ["SAML Provider", "samlprovider", 
     "SAML 2.0 Endpoint for applications which support SAML.", 
    ], 
    ["SCIM Provider", "scimprovider", 
     "SCIM 2.0 provider to create users and groups in external applications", 
    ], 
    ["SAML Provider from Metadata", "", 
     "Create a SAML Provider by importing its Metadata.", 
    ], 
].map(([name, model_name, description]) => ({ name, description, model_name }));

const metadata: Meta<AkApplicationWizardApplicationDetails> = {
    title: "Elements / Application Wizard / Page 1",
    component: "ak-application-wizard-application-details",
    parameters: {
        docs: {
            description: {
                component: "The first page of the application wizard",
            },
        },
        mockData: [
            {
                url: "/api/v3/providers/all/types/",
                method: "GET",
                status: 200,
                response: providerTypes,
            },
        ],
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #fff; padding: 1em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        ${testItem}
    </div>`;

export const PageOne = () => {
    return container(
        html`<ak-application-wizard-context>
            <ak-application-wizard-application-details></ak-application-wizard-application-details>
            <ak-application-context-display-for-test></ak-application-context-display-for-test>
        </ak-application-wizard-context>`
    );
};

export const PageTwo = () => {
    return container(
        html`<ak-application-wizard-context>
            <ak-application-wizard-authentication-method-choice></ak-application-wizard-authentication-method-choice>
            <ak-application-context-display-for-test></ak-application-context-display-for-test>
        </ak-application-wizard-context>`
    );
};
