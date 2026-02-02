import "@patternfly/patternfly/components/Login/login.css";
import "../CaptchaStage.js";

import { flowFactory } from "#stories/flow-interface";

import { Meta } from "@storybook/web-components";

export default {
    title: "Flow / Stages / <ak-stage-captcha> / greCAPTCHA",
} satisfies Meta<typeof import("../CaptchaStage.js").CaptchaStage>;

export const ChallengeRecaptcha = flowFactory("ak-stage-captcha", {
    jsUrl: "https://www.google.com/recaptcha/api.js",
    siteKey: "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
    interactive: true,
});
