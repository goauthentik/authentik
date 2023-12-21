import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import { ApplicationWizard } from "../ak-application-wizard";
import "../ak-application-wizard";
import { mockData } from "./mockData";

const metadata: Meta<ApplicationWizard> = {
    title: "Elements / Application Wizard Implementation / Main",
    component: "ak-application-wizard",
    parameters: {
        docs: {
            description: {
                component: "The first page of the application wizard",
            },
        },
        mockData,
    },
};

const LIGHT = "pf-t-light";
function injectTheme() {
    setTimeout(() => {
        if (!document.body.classList.contains(LIGHT)) {
            document.body.classList.add(LIGHT);
        }
    });
}

export default metadata;

const container = (testItem: TemplateResult) => {
    injectTheme();
    return html` <div style="background: #fff; padding: 1.0rem;">
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
};

export const MainPage = () => {
    return container(html`
        <ak-application-wizard></ak-application-wizard>
        <hr />
        <ak-application-context-display-for-test></ak-application-context-display-for-test>
    `);
};
