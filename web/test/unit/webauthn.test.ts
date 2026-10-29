import { transformNewAssertionForServer } from "#common/helpers/webauthn";

import { describe, expect, it } from "vitest";

function makeCredential(getTransports?: () => string[]): PublicKeyCredential {
    return {
        id: "AQID",
        rawId: new Uint8Array([1, 2, 3]).buffer,
        type: "public-key",
        response: {
            clientDataJSON: new Uint8Array([4, 5, 6]).buffer,
            attestationObject: new Uint8Array([7, 8, 9]).buffer,
            getTransports,
        },
        getClientExtensionResults: () => ({}),
    } as unknown as PublicKeyCredential;
}

describe("transformNewAssertionForServer", () => {
    it.each(
        [["hybrid"], ["usb", "nfc"], ["internal", "hybrid"], ["future-transport"], []].map(
            (transports) => ({ transports }),
        ),
    )(
        "preserves the reported transport list $transports in the registration response",
        ({ transports }) => {
            const credential = makeCredential(() => transports);

            const assertion = transformNewAssertionForServer(credential);

            expect(assertion.response).toEqual({
                clientDataJSON: "BAUG",
                attestationObject: "BwgJ",
                transports,
            });
        },
    );

    it("returns an empty transport list when the client does not implement getTransports", () => {
        const assertion = transformNewAssertionForServer(makeCredential());

        expect(assertion.response.transports).toEqual([]);
    });
});
