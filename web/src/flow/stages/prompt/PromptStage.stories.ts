import "@patternfly/patternfly/components/Login/login.css";
import "../../../stories/flow-interface.js";
import "./PromptStage.js";

import {
    ContextualFlowInfoLayoutEnum,
    PromptChallenge,
    PromptTypeEnum,
    UiThemeEnum,
} from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / Stages / <ak-stage-prompt>",
};

function promptFactory(challenge: PromptChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface-flow theme=${theme}>
                <ak-stage-prompt .challenge=${challenge}></ak-stage-prompt>
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

export const ChallengeDefault = promptFactory({
    flowInfo: {
        title: "<ak-stage-prompt>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
    fields: [],
});

export const AllFieldTypes = promptFactory({
    flowInfo: {
        title: "<ak-stage-prompt>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
    fields: [
        PromptTypeEnum.Text,
        PromptTypeEnum.TextArea,
        PromptTypeEnum.TextReadOnly,
        PromptTypeEnum.TextAreaReadOnly,
        PromptTypeEnum.Username,
        PromptTypeEnum.Email,
        PromptTypeEnum.Password,
        PromptTypeEnum.Number,
        PromptTypeEnum.Checkbox,
        PromptTypeEnum.RadioButtonGroup,
        PromptTypeEnum.Dropdown,
        PromptTypeEnum.Date,
        PromptTypeEnum.DateTime,
        PromptTypeEnum.File,
        PromptTypeEnum.Separator,
        PromptTypeEnum.Hidden,
        PromptTypeEnum.Static,
        PromptTypeEnum.AkLocale,
    ].map((type, idx) => {
        return {
            fieldKey: `fk_${type}`,
            type: type,
            label: `label_${type}`,
            order: idx,
            required: true,
            placeholder: `pl_${type}`,
            initialValue: `iv_${type}`,
            subText: `st_${type}`,
            choices: [],
        };
    }),
});
