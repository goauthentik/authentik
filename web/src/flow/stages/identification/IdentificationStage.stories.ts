import "@patternfly/patternfly/components/Login/login.css";
import "../../../stories/flow-interface.js";
import "./IdentificationStage.js";

import { FlowDesignationEnum, IdentificationChallenge, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / Stages / <ak-stage-identification>",
};

function identificationFactory(challenge: IdentificationChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface-flow theme=${theme}>
                <ak-stage-identification .challenge=${challenge}></ak-stage-identification>
            </ak-storybook-interface-flow>`;
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
    flowInfo: {
        layout: "stacked",
        cancelUrl: "",
        title: "Foo",
    },
});

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengePassword = identificationFactory({
    userFields: ["username"],
    passwordFields: true,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
    showSourceLabels: false,
    flowInfo: {
        layout: "stacked",
        cancelUrl: "",
        title: "Foo",
    },
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

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengePasswordCaptchaTurnstileVisible = identificationFactory({
    userFields: ["username"],
    passwordFields: true,
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

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengeEverything = identificationFactory({
    userFields: ["username"],
    passwordFields: true,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
    showSourceLabels: false,
    allowShowPassword: true,
    passwordlessUrl: "qwer",
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
    sources: [
        {
            name: "Google",
            challenge: {
                component: "xak-flow-redirect",
                to: "foo",
            },
            iconUrl: "/static/authentik/sources/google.svg",
        },
    ],
    recoveryUrl: "foo",
    enrollUrl: "bar",
});
