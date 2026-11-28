import "#flow/stages/prompt/PromptStage";
import type { PromptStage } from "#flow/stages/prompt/PromptStage";
import type { StageHost } from "#flow/types";

import { StagePrompt } from "@goauthentik/api";

import { vi } from "vitest";

const mounted = new Set<HTMLElement>();

/**
 * A prompt with the generated client's required fields filled with empty defaults.
 */
export function stagePrompt(
    init: Pick<StagePrompt, "fieldKey" | "type"> & Partial<StagePrompt>,
): StagePrompt {
    return {
        label: init.fieldKey,
        required: false,
        placeholder: "",
        initialValue: "",
        order: 0,
        subText: "",
        choices: null,
        ...init,
    };
}

/**
 * Mounts an `<ak-stage-prompt>` with a simple host & challenge, and hooks the submit function so we
 * can check the result.
 */
export async function mountPromptStage(fields: StagePrompt[]) {
    const submit = vi.fn<StageHost["submit"]>().mockResolvedValue(true);
    const stage = document.createElement("ak-stage-prompt") as PromptStage;

    stage.host = { loading: false, submit };
    stage.challenge = { component: "ak-stage-prompt", fields };

    document.body.append(stage);
    mounted.add(stage);

    await stage.updateComplete;

    return { stage, submit };
}

export function unmountPromptStages() {
    for (const element of mounted) element.remove();
    mounted.clear();
}
