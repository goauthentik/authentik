import "@patternfly/patternfly/components/Login/login.css";
import "../CaptchaStage.js";

import { flowFactory } from "#stories/flow-interface";

import { Meta } from "@storybook/web-components";

export default {
    title: "Flow / Stages / <ak-stage-captcha> / hCaptcha",
} satisfies Meta<typeof import("../CaptchaStage.js").CaptchaStage>;

export const VisibleChallengePasses = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        siteKey: "10000000-ffff-ffff-ffff-000000000001",
        interactive: true,
    },
    {
        name: "Visible Challenge - Always Passes",
    },
);

export const EnterpriseAccountSafe = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        siteKey: "20000000-ffff-ffff-ffff-000000000002",
        interactive: true,
    },
    {
        name: "Enterprise Account - Safe",
    },
);

export const EnterpriseAccountBotDetected = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        siteKey: "30000000-ffff-ffff-ffff-000000000003",
        interactive: true,
    },
    {
        name: "Enterprise Account - Bot Detected",
    },
);

export const InvisibleChallengePasses = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        siteKey: "10000000-ffff-ffff-ffff-000000000001",
        interactive: false,
    },
    {
        name: "Invisible Challenge - Always Passes",
    },
);

export const InvisibleEnterpriseAccountBotDetected = flowFactory(
    "ak-stage-captcha",
    {
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        siteKey: "30000000-ffff-ffff-ffff-000000000003",
        interactive: false,
    },
    {
        name: "Invisible Enterprise Account - Bot Detected",
    },
);
