import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "@patternfly/patternfly/components/Login/login.css";

import { CaptchaChallenge, UiThemeEnum } from "@goauthentik/api";

import "../../../stories/flow-interface";
import "./CaptchaStage";

export default {
    title: "Flow / Stages / Captcha",
};

export const LoadingNoChallenge = () => {
    return html`<ak-storybook-interface theme=${UiThemeEnum.Dark}>
        <div class="pf-c-login">
            <div class="pf-c-login__container">
                <div class="pf-c-login__main">
                    <ak-stage-captcha></ak-stage-captcha>
                </div>
            </div>
        </div>
    </ak-storybook-interface>`;
};

function captchaFactory(challenge: CaptchaChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface theme=${theme}>
                <div class="pf-c-login">
                    <div class="pf-c-login__container">
                        <div class="pf-c-login__main">
                            <ak-stage-captcha .challenge=${challenge}></ak-stage-captcha>
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

export const ChallengeHCaptcha = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://js.hcaptcha.com/1/api.js",
    siteKey: "10000000-ffff-ffff-ffff-000000000001",
    interactive: true,
} as CaptchaChallenge);

// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
export const ChallengeTurnstileVisible = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
    siteKey: "1x00000000000000000000AA",
    interactive: true,
} as CaptchaChallenge);
export const ChallengeTurnstileInvisible = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
    siteKey: "1x00000000000000000000BB",
    interactive: true,
} as CaptchaChallenge);
export const ChallengeTurnstileForce = captchaFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
    siteKey: "3x00000000000000000000FF",
    interactive: true,
} as CaptchaChallenge);
