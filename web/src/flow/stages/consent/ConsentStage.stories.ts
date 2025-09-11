import "@patternfly/patternfly/components/Login/login.css";
import "../../../stories/flow-interface.js";
import "./ConsentStage.js";

import { ConsentChallenge, ContextualFlowInfoLayoutEnum, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / Stages / <ak-stage-consent>",
};

function consentFactory(challenge: ConsentChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface-flow theme=${theme}>
                <ak-stage-consent .challenge=${challenge}></ak-stage-consent>
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

export const NewConsent = consentFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    flowInfo: {
        title: "<ak-stage-consent>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
    headerText: "lorem ipsum",
    token: "",
    permissions: [
        { name: "Perm 1", id: "perm_1" },
        { name: "Perm 2", id: "perm_2" },
        { name: "Perm 3", id: "perm_3" },
    ],
    additionalPermissions: [],
});

export const ExistingConsentNewPermissions = consentFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    flowInfo: {
        title: "<ak-stage-consent>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
    headerText: "lorem ipsum",
    token: "",
    permissions: [
        { name: "Perm 1", id: "perm_1" },
        { name: "Perm 2", id: "perm_2" },
        { name: "Perm 3", id: "perm_3" },
    ],
    additionalPermissions: [{ name: "Perm 4", id: "perm_4" }],
});
