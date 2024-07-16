import Page from "../page.js";

export class LdapForm extends Page {
    async setBindFlow(selector: string) {
        await this.searchSelect(
            "[name=authorizationFlow]",
            "authorizationFlow",
            `div*=${selector}`,
        );
    }
}

export default new LdapForm();
