import "@patternfly/patternfly/components/Login/login.css";
import "../CaptchaStage.js";

import { flowFactory } from "#stories/flow-interface";

import { Meta } from "@storybook/web-components";

export default {
    title: "Flow / Stages / <ak-stage-captcha> / Turnstile",
} satisfies Meta<typeof import("../CaptchaStage.js").CaptchaStage>;

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const VisibleChallengePasses = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        siteKey: "1x00000000000000000000AA",
        interactive: true,
    },
    {
        name: "Visible Challenge - Always Passes",
    },
);

export const VisibleChallengeFails = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        siteKey: "2x00000000000000000000AB",
        interactive: true,
    },
    {
        name: "Visible Challenge - Always Fails",
    },
);

export const InvisibleChallengePasses = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        siteKey: "1x00000000000000000000BB",
        interactive: false,
    },
    {
        name: "Invisible Challenge (Passes)",
    },
);

export const InvisibleChallengeFails = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        siteKey: "2x00000000000000000000BB",
        interactive: false,
    },
    {
        name: "Invisible Challenge (Fails)",
    },
);

export const ForcedInteractiveChallenge = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        siteKey: "3x00000000000000000000FF",
        interactive: true,
    },
    {
        name: "Forced Interactive Challenge",
    },
);
