import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-app-icon";
import AkAppIcon from "../ak-app-icon";

const metadata: Meta<AkAppIcon> = {
    title: "Components / App Icon",
    component: "ak-app-icon",
    parameters: {
        docs: {
            description: {
                component: "A small card displaying an application icon",
            },
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #000; padding: 2em">
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

export const AppIcon = () => {
    return container(html`<ak-app-icon .app=${{ name: "Demo app" }} size="pf-m-md"></ak-app-icon>`);
};
