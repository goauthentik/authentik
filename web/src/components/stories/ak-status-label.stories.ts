import "#elements/messages/MessageContainer";
import "../ak-status-label.js";

import AkStatusLabel from "../ak-status-label.js";

import { Meta } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const metadata: Meta<AkStatusLabel> = {
    title: "Components / App Status Label",
    component: "ak-status-label",
    parameters: {
        docs: {
            description: {
                component: "A status label display",
            },
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) => html`
    <style>
        dl {
            display: grid;
            grid-template-columns: 22ch 1fr;
            gap: 0.5rem;
        }
    </style>
    ${testItem}
`;

export const AppIcon = () => {
    // prettier-ignore
    return container(html`
        <dl>
            <dt>Good</dt><dd>

                <ak-status-label good></ak-status-label>

           </dd>
            <dt>Bad (Default)</dt><dd>

                <ak-status-label></ak-status-label>

           </dd>
            <dt>Programmatically Good</dt><dd>

                <ak-status-label good></ak-status-label>

           </dd>
            <dt>Programmatically Bad</dt><dd>

                <ak-status-label ?good=${false}></ak-status-label>

           </dd>
            <dt>Good Warning</dt><dd>

                <ak-status-label type="warning" good></ak-status-label>

           </dd>
            <dt>Bad Warning</dt><dd>

                <ak-status-label type="warning"></ak-status-label>

           </dd>
            <dt>Good Info</dt><dd>

                <ak-status-label type="info" good></ak-status-label>

           </dd>
            <dt>Bad Info</dt><dd>

                <ak-status-label type="info"></ak-status-label>

           </dd>
            <dt>Good With Alternative Message</dt><dd>

                <ak-status-label good good-label="Hurray!" bad-label="Boo!"></ak-status-label>

           </dd>
            <dt>Bad with Alternative Message</dt><dd>

                <ak-status-label good-label="Hurray!" bad-label="Boo!"></ak-status-label>

            </dd>
            <dt>Good, Compact</dt><dd>

                <ak-status-label good compact></ak-status-label>

           </dd>
           <dt>Bad, Compact</dt><dd>

                <ak-status-label compact></ak-status-label>

           </dd>
        </dl>
    `);
};
