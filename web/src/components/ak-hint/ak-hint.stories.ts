import { MessageLevel } from "@goauthentik/common/messages";
import "@goauthentik/elements/buttons/ActionButton/ak-action-button";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-radio-input";
import "./ak-hint";
import AkHint from "./ak-hint";
import "./ak-hint-body";
import "./ak-hint-title";

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
    html` <div style="background: #fff; padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                color: black;
                margin-top: 1em;
            }

            * {
                --ak-hint--Color: black !important;
            }
            ak-hint-title::part(ak-hint-title),
            ak-hint-footer::part(ak-hint-footer),
            slotted::(*) {
                color: black;
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
