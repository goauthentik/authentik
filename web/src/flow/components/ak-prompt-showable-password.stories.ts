import "@patternfly/patternfly/components/Login/login.css";
import "#flow/stages/prompt/PromptStage";
import { flowFactory } from "#stories/flow-interface";

import { PromptTypeEnum } from "@goauthentik/api";

export default {
    title: "Flow / Components / <ak-prompt-showable-password>",
};

// Renders a demo of both a regular password and a showable password.
export const Default = flowFactory("ak-stage-prompt", {
    fields: [
        {
            fieldKey: "password",
            type: PromptTypeEnum.Password,
            label: "Password (standard)",
            order: 0,
            required: true,
            placeholder: "Password",
            choices: [],
        },
        {
            fieldKey: "password_viewable",
            type: PromptTypeEnum.PasswordViewable,
            label: "Password (viewable)",
            order: 1,
            required: true,
            placeholder: "Password",
            choices: [],
        },
    ],
});
