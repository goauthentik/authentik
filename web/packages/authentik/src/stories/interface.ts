import { Interface } from "@goauthentik/elements/Interface/index.js";

import { customElement, property } from "lit/decorators.js";

import { UiThemeEnum } from "@goauthentik/api";

@customElement("ak-storybook-interface")
export class StoryInterface extends Interface {
    @property()
    storyTheme: UiThemeEnum = UiThemeEnum.Dark;

    async getTheme(): Promise<UiThemeEnum> {
        return this.storyTheme;
    }
}
