import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-application-wizard-application-details";
import AkApplicationWizardApplicationDetails from "../ak-application-wizard-application-details";
import "../ak-application-wizard-context";
import "./ak-application-context-display-for-test";

const metadata: Meta<AkApplicationWizardApplicationDetails> = {
    title: "Elements / Application Wizard / Page 1",
    component: "ak-application-wizard-application-details",
    parameters: {
        docs: {
            description: {
                component: "The first page of the application wizard",
            },
        },
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
