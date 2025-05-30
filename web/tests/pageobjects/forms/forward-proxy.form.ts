/// <reference types="@wdio/globals/types" />
import { searchSelect } from "#tests/utils/controls";

export abstract class ForwardProxyForm {
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
}

export default ForwardProxyForm;
