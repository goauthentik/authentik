import { FlowExecutor } from "#flow/FlowExecutor";

import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-storybook-interface-flow")
export class StoryFlowInterface extends FlowExecutor {
    public override firstUpdated() {
        return Promise.resolve();
    }

    public override submit = () => {
        return Promise.resolve(true);
    };

    async renderChallenge(): Promise<TemplateResult> {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-storybook-interface-flow": StoryFlowInterface;
    }
}
