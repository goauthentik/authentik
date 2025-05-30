/// <reference types="@wdio/globals/types" />
import { searchSelect } from "#tests/utils/controls";

export abstract class TransparentProxyForm {
    public static setAuthorizationFlow(selector: string) {
        return searchSelect(
            'ak-flow-search[name="authorizationFlow"]',
            "authorizationFlow",
            selector,
        );
    }

    public static get $externalHost() {
        return $('input[name="externalHost"]');
    }

    public static get $internalHost() {
        return $('input[name="internalHost"]');
    }
}

export default TransparentProxyForm;
