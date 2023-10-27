import Page from "../page.js";
import { $ } from "@wdio/globals";

export class SamlForm extends Page {
    async setAuthorizationFlow(selector: string) {
        await this.searchSelect(
            '>>>ak-flow-search[name="authorizationFlow"] input[type="text"]',
            "authorizationFlow",
            `button*=${selector}`,
        );
    }

    get acsUrl() {
        return $('>>>input[name="acsUrl"]');
    }
}

export default new SamlForm();
