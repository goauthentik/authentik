import Page from "../page.js";

export class LdapForm extends Page {
    async setBindFlow(selector: string) {
        await this.searchSelect(
            '>>>ak-tenanted-flow-search[name="authorizationFlow"] input[type="text"]',
            "authorizationFlow",
            `button*=${selector}`,
        );
    }
}

export default new LdapForm();
