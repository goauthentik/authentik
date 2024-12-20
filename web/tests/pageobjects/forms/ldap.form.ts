import Page from "../page.js";

export class LdapForm extends Page {
    async setBindFlow() {
        await this.searchSelect(
            '>>>ak-search-select-view[name="authorizationFlow"]',
            "authorizationFlow",
            "default-authentication-flow",
        );
    }
}

export default new LdapForm();
