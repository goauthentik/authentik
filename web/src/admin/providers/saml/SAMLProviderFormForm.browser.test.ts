import { ArrayInput } from "#elements/ak-array-input";

import { SAMLProviderACSURL } from "#admin/providers/saml/SAMLProviderACSURL";
import { renderForm, SAMLProviderFormProps } from "#admin/providers/saml/SAMLProviderFormForm";

import {
    CryptoApi,
    FlowsApi,
    PropertymappingsApi,
    ProvidersApi,
    SAMLACSURL,
    SAMLLogoutMethods,
} from "@goauthentik/api";

import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { render } from "lit";

const mounted = new Set<HTMLFormElement>();

beforeEach(() => {
    const empty = {
        results: [],
        pagination: {
            next: 0,
            previous: 0,
            count: 0,
            current: 1,
            totalPages: 1,
            startIndex: 0,
            endIndex: 0,
        },
    };

    vi.spyOn(FlowsApi.prototype, "flowsInstancesList").mockResolvedValue(empty);
    vi.spyOn(CryptoApi.prototype, "cryptoCertificatekeypairsList").mockResolvedValue(empty);

    vi.spyOn(PropertymappingsApi.prototype, "propertymappingsProviderSamlList").mockResolvedValue(
        empty,
    );

    vi.spyOn(ProvidersApi.prototype, "providersOauth2List").mockResolvedValue(empty);
});

afterEach(() => {
    mounted.forEach((form) => form.remove());
    mounted.clear();
    vi.restoreAllMocks();
});

async function mount(provider?: SAMLProviderFormProps["provider"]) {
    const form = document.body.appendChild(document.createElement("form"));
    mounted.add(form);

    const props: SAMLProviderFormProps = {
        provider,
        setHasSigningKp: vi.fn(),
        hasSigningKp: false,
        signingKeyType: null,
        setHasEncryptionKp: vi.fn(),
        hasEncryptionKp: false,
        setHasSlsUrl: vi.fn(),
        hasSlsUrl: false,
        setSlsBinding: vi.fn(),
        hasPostBinding: false,
        logoutMethod: SAMLLogoutMethods.FrontchannelIframe,
        setLogoutMethod: vi.fn(),
    };

    const renderHost = async (changes: Partial<SAMLProviderFormProps> = {}) => {
        Object.assign(props, changes);
        render(renderForm(props), form);
        const array = form.querySelector<ArrayInput<SAMLACSURL>>("ak-array-input")!;
        await array.updateComplete;

        return array;
    };

    return { array: await renderHost(), renderHost };
}

it("keeps new-provider ACS edits and added rows when other settings change", async () => {
    const { array, renderHost } = await mount();
    const row = array.renderRoot.querySelector<SAMLProviderACSURL>("ak-provider-saml-acs-url")!;
    const url = row.renderRoot.querySelector<HTMLInputElement>('input[name="url"]')!;
    url.value = "https://sp.example.com/acs";
    url.dispatchEvent(new Event("change", { bubbles: true }));
    await array.updateComplete;
    array.renderRoot.querySelector<HTMLButtonElement>("button.pf-m-link")!.click();
    await array.updateComplete;
    expect(array.toJSON()).toHaveLength(2);
    await renderHost({ hasSlsUrl: true, hasSigningKp: true });
    expect(array.toJSON()).toHaveLength(2);
    expect(array.toJSON()[0].url).toBe("https://sp.example.com/acs");
});

it("keeps row removals on render and replaces rows when another provider loads", async () => {
    const { array, renderHost } = await mount({ acsUrl: "https://sp.example.com/old" });
    array.renderRoot.querySelector<HTMLButtonElement>("button.pf-m-control")!.click();
    await array.updateComplete;
    await renderHost({ hasSlsUrl: true });
    expect(array.toJSON()).toEqual([]);
    await renderHost({ provider: { acsUrls: [{ url: "https://sp.example.com/new" }] } });
    expect(array.toJSON()).toEqual([{ url: "https://sp.example.com/new" }]);
});
