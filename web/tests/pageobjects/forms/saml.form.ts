import { searchSelect } from "#tests/utils/controls";
import { $ } from "@wdio/globals";

export abstract class SAMLForm {
    public static setAuthorizationFlow(buttonText: string) {
        return searchSelect(
            'ak-flow-search[name="authorizationFlow"]',
            "authorizationFlow",
            buttonText,
        );
    }

    public static get $ASCURL() {
        return $('input[name="acsUrl"]');
    }
}

export default SAMLForm;
