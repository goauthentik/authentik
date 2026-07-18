import "@patternfly/patternfly/components/Login/login.css";
import "./PromptStage.js";

import { flowFactory } from "#stories/flow-interface";

import { PromptTypeEnum } from "@goauthentik/api";

import { capitalCase } from "change-case";

export default {
    title: "Flow / Stages / <ak-stage-prompt>",
};

export const ChallengeDefault = flowFactory("ak-stage-prompt", {
    fields: [],
});

export const AllFieldTypes = flowFactory("ak-stage-prompt", {
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
            label: `${capitalCase(type)} (${type})`,
            order: idx,
            required: true,
            placeholder: `Placeholder (${type})`,
            initialValue: `initial_value_${type}`,
            subText: `Subtext (${type})`,
            choices: [],
        };
    }),
});
