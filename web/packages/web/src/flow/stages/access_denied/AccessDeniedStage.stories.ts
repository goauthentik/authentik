import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "@patternfly/patternfly/components/Login/login.css";

import { AccessDeniedChallenge, ChallengeChoices, UiThemeEnum } from "@goauthentik/api";

import "../../../stories/flow-interface";
import "./AccessDeniedStage";

export default {
    title: "Flow / Stages / AccessDeniedStage",
};

export const LoadingNoChallenge = () => {
    return html`<ak-storybook-interface theme=${UiThemeEnum.Dark}>
        <div class="pf-c-login">
            <div class="pf-c-login__container">
                <div class="pf-c-login__main">
                    <ak-stage-access-denied></ak-stage-access-denied>
                </div>
            </div>
        </div>
    </ak-storybook-interface>`;
};

export const Challenge: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface theme=${theme}>
            <div class="pf-c-login">
                <div class="pf-c-login__container">
                    <div class="pf-c-login__main">
                        <ak-stage-access-denied .challenge=${challenge}></ak-stage-access-denied>
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
            errorMessage: "This is an error message",
        } as AccessDeniedChallenge,
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
