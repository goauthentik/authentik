import "@patternfly/patternfly/components/Login/login.css";
import "../../../stories/flow-interface.js";
import "./CaptchaStage.js";

import { CaptchaChallenge, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / Stages / <ak-stage-captcha>",
};

function captchaFactory(challenge: CaptchaChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface-flow theme=${theme}>
                <ak-stage-captcha .challenge=${challenge}></ak-stage-captcha>
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

export const ChallengeHCaptcha = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://js.hcaptcha.com/1/api.js",
    siteKey: "10000000-ffff-ffff-ffff-000000000001",
    interactive: true,
    flowInfo: {
        layout: "stacked",
        cancelUrl: "",
        title: "Foo",
    },
});

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengeTurnstileVisible = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
    siteKey: "1x00000000000000000000AA",
    interactive: true,
    flowInfo: {
        layout: "stacked",
        cancelUrl: "",
        title: "Foo",
    },
});
export const ChallengeTurnstileInvisible = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
    siteKey: "1x00000000000000000000BB",
    interactive: true,
    flowInfo: {
        layout: "stacked",
        cancelUrl: "",
        title: "Foo",
    },
});
export const ChallengeTurnstileForce = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
    siteKey: "3x00000000000000000000FF",
    interactive: true,
    flowInfo: {
        layout: "stacked",
        cancelUrl: "",
        title: "Foo",
    },
});

export const ChallengeRecaptcha = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://www.google.com/recaptcha/api.js",
    siteKey: "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
    interactive: true,
    flowInfo: {
        layout: "stacked",
        cancelUrl: "",
        title: "Foo",
    },
});
