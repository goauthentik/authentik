/// <reference types="@wdio/globals/types" />
import { searchSelect } from "#tests/utils/controls";

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
