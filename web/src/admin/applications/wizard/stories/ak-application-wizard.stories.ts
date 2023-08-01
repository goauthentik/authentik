import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-application-wizard-application-details";
import AkApplicationWizardApplicationDetails from "../ak-application-wizard-application-details";
import "../ak-application-wizard-authentication-method-choice";
import "../ak-application-wizard-context";
import "../ldap/ak-application-wizard-authentication-by-ldap";
import "./ak-application-context-display-for-test";
import {
    dummyAuthenticationFlowsSearch,
    dummyCoreGroupsSearch,
    dummyCryptoCertsSearch,
    dummyProviderTypesList,
} from "./samples";

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
                response: dummyProviderTypesList,
            },
            {
                url: "/api/v3/core/groups/?ordering=name",
                method: "GET",
                status: 200,
                response: dummyCoreGroupsSearch,
            },

            {
                url: "/api/v3/crypto/certificatekeypairs/?has_key=true&include_details=false&ordering=name",
                method: "GET",
                status: 200,
                response: dummyCryptoCertsSearch,
            },
            {
                url: "/api/v3/flows/instances/?designation=authentication&ordering=slug",
                method: "GET",
                status: 200,
                response: dummyAuthenticationFlowsSearch,
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
        </ak-application-wizard-context>`,
    );
};

export const PageTwo = () => {
    return container(
        html`<ak-application-wizard-context>
            <ak-application-wizard-authentication-method-choice></ak-application-wizard-authentication-method-choice>
            <ak-application-context-display-for-test></ak-application-context-display-for-test>
        </ak-application-wizard-context>`,
    );
};

export const PageThreeLdap = () => {
    return container(
        html`<ak-application-wizard-context>
            <ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>
            <ak-application-context-display-for-test></ak-application-context-display-for-test>
        </ak-application-wizard-context>`,
    );
};
