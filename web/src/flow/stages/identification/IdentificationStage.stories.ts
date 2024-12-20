import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "@patternfly/patternfly/components/Login/login.css";

import { FlowDesignationEnum, IdentificationChallenge, UiThemeEnum } from "@goauthentik/api";

import "../../../stories/flow-interface";
import "./IdentificationStage";

export default {
    title: "Flow / Stages / Identification",
};

export const LoadingNoChallenge = () => {
    return html`<ak-storybook-interface theme=${UiThemeEnum.Dark}>
        <div class="pf-c-login">
            <div class="pf-c-login__container">
                <div class="pf-c-login__main">
                    <ak-stage-identification></ak-stage-identification>
                </div>
            </div>
        </div>
    </ak-storybook-interface>`;
};

function identificationFactory(challenge: IdentificationChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface theme=${theme}>
                <div class="pf-c-login">
                    <div class="pf-c-login__container">
                        <div class="pf-c-login__main">
                            <ak-stage-identification
                                .challenge=${challenge}
                            ></ak-stage-identification>
                        </div>
                    </div></div
            ></ak-storybook-interface>`;
        },
        args: {
            theme: "automatic",
            challenge: challenge,
        },
        argTypes: {
            theme: {
                options: [UiThemeEnum.Automatic, UiThemeEnum.Light, UiThemeEnum.Dark],
                control: {
                    type: "select",
                },
            },
        },
    };
}

export const ChallengeDefault = identificationFactory({
    userFields: ["username"],
    passwordFields: false,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
    showSourceLabels: false,
    // jsUrl: "https://js.hcaptcha.com/1/api.js",
    // siteKey: "10000000-ffff-ffff-ffff-000000000001",
    // interactive: true,
});

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengeCaptchaTurnstileVisible = identificationFactory({
    userFields: ["username"],
    passwordFields: false,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
    showSourceLabels: false,
    flowInfo: {
        layout: "stacked",
        cancelUrl: "",
        title: "Foo",
    },
    captchaStage: {
        pendingUser: "",
        pendingUserAvatar: "",
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        siteKey: "1x00000000000000000000AA",
        interactive: true,
    },
});
