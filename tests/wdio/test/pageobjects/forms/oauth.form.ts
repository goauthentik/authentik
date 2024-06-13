import Page from "../page.js";
import { $ } from "@wdio/globals";

export class OauthForm extends Page {
    async setAuthorizationFlow(selector: string) {
        await this.searchSelect(
            '>>>ak-flow-search[name="authorizationFlow"] input[type="text"]',
            "authorizationFlow",
            `button*=${selector}`,
        );
    }

    get providerName() {
        return $('>>>ak-form-element-horizontal[name="name"] input');
    }
}

export default new OauthForm();
