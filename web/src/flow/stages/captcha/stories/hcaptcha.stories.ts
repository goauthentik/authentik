import "@patternfly/patternfly/components/Login/login.css";
import "../CaptchaStage.js";

import { flowFactory } from "#stories/flow-interface";

import { Meta } from "@storybook/web-components";

export default {
    title: "Flow / Stages / <ak-stage-captcha> / hCaptcha",
} satisfies Meta<typeof import("../CaptchaStage.js").CaptchaStage>;

export const ChallengeHCaptcha = flowFactory("ak-stage-captcha", {
    jsUrl: "https://js.hcaptcha.com/1/api.js",
    siteKey: "10000000-ffff-ffff-ffff-000000000001",
    interactive: true,
});
