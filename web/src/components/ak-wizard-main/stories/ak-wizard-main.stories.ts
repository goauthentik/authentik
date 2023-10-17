import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";
import "./ak-demo-wizard";

const metadata: Meta<AkWizard> = {
    title: "Components / Wizard / Basic",
    component: "ak-wizard-main",
    parameters: {
        docs: {
            description: {
                component: "A container for our wizard.",
            },
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #fff; padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        <ak-message-container></ak-message-container>
        ${testItem}
    </div>`;


export const OnePageWizard = () => {
    return container(
        html` <ak-demo-wizard></ak-demo-wizard>`
    );
};
