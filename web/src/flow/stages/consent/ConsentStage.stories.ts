import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "@patternfly/patternfly/components/Login/login.css";

import { ConsentChallenge, ContextualFlowInfoLayoutEnum, UiThemeEnum } from "@goauthentik/api";

import "../../../stories/flow-interface";
import "./ConsentStage";

export default {
    title: "Flow / Stages / <ak-stage-consent>",
};

export const NewConsent: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-stage-consent .challenge=${challenge}></ak-stage-consent>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
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
        } as ConsentChallenge,
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

export const ExistingConsentNewPermissions: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-stage-consent .challenge=${challenge}></ak-stage-consent>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
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
        } as ConsentChallenge,
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
