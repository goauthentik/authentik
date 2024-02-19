import { FlowExecutor } from "@goauthentik/app/flow/FlowExecutor";

import { customElement, property } from "lit/decorators.js";

import { UiThemeEnum } from "@goauthentik/api";

@customElement("ak-storybook-interface-flow")
export class StoryFlowInterface extends FlowExecutor {
    @property()
    storyTheme: UiThemeEnum = UiThemeEnum.Dark;

    async getTheme(): Promise<UiThemeEnum> {
        return this.storyTheme;
    }
}
