import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-crypto-certificate-search";
import AkCryptoCertificateSearch from "../ak-crypto-certificate-search";
import { dummyCryptoCertsSearch } from "./samples";

const metadata: Meta<AkCryptoCertificateSearch> = {
    title: "Components / Searches / CryptoCertificateKeyPair",
    component: "ak-crypto-certificate-search",
    parameters: {
        docs: {
            description: {
                component: "A search function for cryptographic certificates in Authentik",
            },
        },
        mockData: [
            {
                url: "/api/v3/crypto/certificatekeypairs/?has_key=true&include_details=false&ordering=name",
                method: "GET",
                status: 200,
                response: dummyCryptoCertsSearch,
            },
        ],
    },
    argTypes: {
        // Typescript is unaware that arguments for components are treated as properties, and
        // properties are typically renamed to lower case, even if the variable is not.
        // @ts-expect-error
        nokey: {
            control: "boolean",
            description:
                "When true, certificates without valid keys will be included in the search",
        },
        singleton: {
            control: "boolean",
            description:
                "Supports the SAML Source search: when true, if there is no certificate in the current form and there is one and only one certificate in the Authentik database, use that certificate by default.",
        },
    },
};

export default metadata;

const LIGHT = "pf-t-light";
function injectTheme() {
    setTimeout(() => {
        if (!document.body.classList.contains(LIGHT)) {
            document.body.classList.add(LIGHT);
        }
    });
}

const container = (testItem: TemplateResult) => {
    injectTheme();
    return html` <div style="background: #fff; padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        <ak-message-container></ak-message-container>
        ${testItem}
        <pre id="message-pad" style="margin-top: 1em"></pre>
    </div>`;
};

export const CryptoCertificateSearch = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const showMessage = (ev: CustomEvent<any>) => {
        const detail = ev.detail;
        delete detail["target"];
        document.getElementById("message-pad")!.innerText = `Event: ${JSON.stringify(
            detail,
            null,
            2,
        )}`;
    };

    return container(
        html` <ak-form-element-horizontal name="test-crypto-certificate-search">
            <ak-crypto-certificate-search @ak-change=${showMessage}></ak-crypto-certificate-search
        ></ak-form-element-horizontal>`,
    );
};
