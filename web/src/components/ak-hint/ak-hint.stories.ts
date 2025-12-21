import "#components/ak-hint/ak-hint-footer";
import "#elements/buttons/ActionButton/ak-action-button";
import "../ak-radio-input.js";
import "./ak-hint-body.js";
import "./ak-hint-title.js";
import "./ak-hint.js";

import AkHint from "./ak-hint.js";

import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";

import { Meta } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const metadata: Meta<AkHint> = {
    title: "Components / Patternfly Hint",
    component: "ak-hint",
    parameters: {
        docs: {
            description: {
                component: "A stylized hint box",
            },
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="padding: 2em">
        <style>
            li {
                display: block;
            }

            ak-hint {
                --ak-hint--Color: var(--pf-global--Color--dark-100);
            }

            @media (prefers-color-scheme: dark) {
                ak-hint {
                    --ak-hint--Color: var(--pf-global--Color--light-100);
                }
            }

            p {
                margin-top: 1em;
            }
        </style>

        ${testItem}

        <ul id="radio-message-pad" style="margin-top: 1em"></ul>
    </div>`;

export const Default = () => {
    return container(
        html` <section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <ak-hint>
                <ak-hint-body>
                    <p style="padding-bottom: 1rem;">
                        Authentik has a new Application Wizard that can configure both an
                        application and its authentication provider at the same time.
                        <a href="(link to docs)">Learn more about the wizard here.</a>
                    </p>
                    <ak-action-button
                        class="pf-m-secondary"
                        .apiRequest=${() => {
                            showMessage({
                                message: "This would have shown the wizard",
                                level: MessageLevel.success,
                            });
                        }}
                        >Create with Wizard</ak-action-button
                    ></ak-hint-body
                >
            </ak-hint>
        </section>`,
    );
};

export const WithTitle = () => {
    return container(
        html` <section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <ak-hint>
                <ak-hint-title>New Application Wizard</ak-hint-title>
                <ak-hint-body>
                    <p style="padding-bottom: 1rem;">
                        Authentik has a new Application Wizard that can configure both an
                        application and its authentication provider at the same time.
                        <a href="(link to docs)">Learn more about the wizard here.</a>
                    </p>
                    <ak-action-button
                        class="pf-m-secondary"
                        .apiRequest=${() => {
                            showMessage({
                                message: "This would have shown the wizard",
                                level: MessageLevel.success,
                            });
                        }}
                        >Create with Wizard</ak-action-button
                    ></ak-hint-body
                >
            </ak-hint>
        </section>`,
    );
};

export const WithTitleAndFooter = () => {
    return container(
        html` <section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <ak-hint>
                <ak-hint-title>New Application Wizard</ak-hint-title>
                <ak-hint-body>
                    <p style="padding-bottom: 1rem;">
                        Authentik has a new Application Wizard that can configure both an
                        application and its authentication provider at the same time.
                        <a href="(link to docs)">Learn more about the wizard here.</a>
                    </p>
                    <ak-action-button
                        class="pf-m-secondary"
                        .apiRequest=${() => {
                            showMessage({
                                message: "This would have shown the wizard",
                                level: MessageLevel.success,
                            });
                        }}
                        >Create with Wizard</ak-action-button
                    ></ak-hint-body
                >
                <ak-hint-footer
                    ><div style="text-align: right">
                        <input type="checkbox" /> Don't show this message again.
                    </div></ak-hint-footer
                >
            </ak-hint>
        </section>`,
    );
};
