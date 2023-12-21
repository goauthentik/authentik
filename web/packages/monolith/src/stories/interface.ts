import { Interface } from "@goauthentik/app/elements/Base";

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
