import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "@patternfly/patternfly/components/Login/login.css";

import { CaptchaChallenge, ChallengeChoices, UiThemeEnum } from "@goauthentik/api";

import "../../../stories/flow-interface";
import "./CaptchaStage";

export default {
    title: "Flow / Stages / CaptchaStage",
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

export const ChallengeGoogleReCaptcha: StoryObj = {
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
        challenge: {
            type: ChallengeChoices.Native,
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            jsUrl: "https://www.google.com/recaptcha/api.js",
            siteKey: "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
        } as CaptchaChallenge,
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

export const ChallengeHCaptcha: StoryObj = {
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
        challenge: {
            type: ChallengeChoices.Native,
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            jsUrl: "https://js.hcaptcha.com/1/api.js",
            siteKey: "10000000-ffff-ffff-ffff-000000000001",
        } as CaptchaChallenge,
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

export const ChallengeTurnstile: StoryObj = {
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
        challenge: {
            type: ChallengeChoices.Native,
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
            siteKey: "1x00000000000000000000BB",
        } as CaptchaChallenge,
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
