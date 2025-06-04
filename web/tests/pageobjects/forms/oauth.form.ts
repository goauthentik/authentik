import { searchSelect } from "#tests/utils/controls";
import { $ } from "@wdio/globals";

export abstract class OAuthForm {
    public static setAuthorizationFlow(selector: string) {
        return searchSelect(
            'ak-flow-search[name="authorizationFlow"]',
            "authorizationFlow",
            selector,
        );
    }

    public static get $providerName() {
        return $('ak-form-element-horizontal[name="name"]').$("input");
    }
}

export default OAuthForm;
