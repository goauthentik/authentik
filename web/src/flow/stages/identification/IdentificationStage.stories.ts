import "@patternfly/patternfly/components/Login/login.css";
import "./IdentificationStage.js";

import { flowFactory } from "#stories/flow-interface";

import { FlowDesignationEnum } from "@goauthentik/api";

export default {
    title: "Flow / Stages / <ak-stage-identification>",
};

export const ChallengeDefault = flowFactory("ak-stage-identification", {
    userFields: ["username"],
    passwordFields: false,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
});

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengePassword = flowFactory("ak-stage-identification", {
    userFields: ["username"],
    passwordFields: true,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
});

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengeCaptchaTurnstileVisible = flowFactory("ak-stage-identification", {
    userFields: ["username"],
    passwordFields: false,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
    showSourceLabels: false,
    captchaStage: {
        pendingUser: "",
        pendingUserAvatar: "",
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        siteKey: "1x00000000000000000000AA",
        interactive: true,
    },
});

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengePasswordCaptchaTurnstileVisible = flowFactory("ak-stage-identification", {
    userFields: ["username"],
    passwordFields: true,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
    showSourceLabels: false,
    captchaStage: {
        pendingUser: "",
        pendingUserAvatar: "",
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        siteKey: "1x00000000000000000000AA",
        interactive: true,
    },
});

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengeEverything = flowFactory("ak-stage-identification", {
    userFields: ["username"],
    passwordFields: true,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Login",
    showSourceLabels: false,
    allowShowPassword: true,
    passwordlessUrl: "qwer",
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
