import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "@patternfly/patternfly/components/Login/login.css";

import { AccessDeniedChallenge, UiThemeEnum } from "@goauthentik/api";

import "../../../stories/flow-interface";
import "./AccessDeniedStage";

export default {
    title: "Flow / Stages / <ak-stage-access-denied>",
};

export const Challenge: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-stage-access-denied .challenge=${challenge}></ak-stage-access-denied>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            errorMessage: "This is an error message",
            flowInfo: {
                title: "lorem ipsum foo bar baz",
            },
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
