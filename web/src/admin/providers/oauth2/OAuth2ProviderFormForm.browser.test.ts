import type { SearchSelect } from "#elements/forms/SearchSelect/ak-search-select";

import { renderForm } from "#admin/providers/oauth2/OAuth2ProviderFormForm";

import {
    type CertificateKeyPair,
    CertificateKeyPairKeyTypeEnum,
    type OAuth2Provider,
} from "@goauthentik/api";

import { afterEach, describe, expect, it, vi } from "vitest";

import { render } from "lit";

const certificate: CertificateKeyPair = {
    pk: "00000000-0000-0000-0000-000000000001",
    name: "JWT signing certificate",
    fingerprintSha256: null,
    fingerprintSha1: null,
    certExpiry: null,
    certSubject: null,
    privateKeyAvailable: true,
    keyType: CertificateKeyPairKeyTypeEnum.Rsa,
    certificateDownloadUrl: "",
    privateKeyDownloadUrl: "",
    managed: null,
};

const mounted = new Set<HTMLElement>();

async function mountSigningKey(
    provider: Partial<OAuth2Provider>,
): Promise<SearchSelect<CertificateKeyPair>> {
    const container = document.createElement("div");

    render(
        renderForm({
            provider,
            showLogoutMethod: false,
            showLogoutMethodCallback: () => undefined,
        }),
        container,
    );

    const element = container.querySelector<SearchSelect<CertificateKeyPair>>(
        'ak-search-select[name="signingKey"]',
    )!;

    vi.spyOn(element.source!, "fetchObjects").mockResolvedValue([certificate]);

    // Connect only the signing field so unrelated form fields do not fetch data.
    const form = document.body.appendChild(document.createElement("form"));
    mounted.add(form);
    form.appendChild(element);
    await element.settled;

    return element;
}

function inputValue(element: SearchSelect<CertificateKeyPair>): string {
    return element.renderRoot.querySelector<HTMLInputElement>("input")!.value;
}

afterEach(() => {
    for (const container of mounted) container.remove();
    mounted.clear();
    vi.restoreAllMocks();
});

describe("OAuth2 provider signing key", () => {
    it("leaves an existing provider without a signing key empty when one certificate is available", async () => {
        const element = await mountSigningKey({ pk: 1, signingKey: null });

        expect(element.value).toBe("");
        expect(element.selectedObject).toBeNull();
        expect(inputValue(element)).toBe("");
        expect(element.toJSON()).toBeNull();
    });

    it("preselects the only usable signing certificate for a new provider", async () => {
        const element = await mountSigningKey({});

        expect(element.value).toBe(certificate.pk);
        expect(element.selectedObject).toEqual(certificate);
        expect(inputValue(element)).toBe(certificate.name);
        expect(element.toJSON()).toBe(certificate.pk);
    });

    it("keeps an existing provider's signing key empty after clearing it and refreshing the options", async () => {
        const element = await mountSigningKey({ pk: 1, signingKey: certificate.pk });

        expect(inputValue(element)).toBe(certificate.name);
        expect(element.toJSON()).toBe(certificate.pk);

        element.select(null);
        await element.refresh();
        await element.settled;

        expect(element.value).toBe("");
        expect(element.selectedObject).toBeNull();
        expect(inputValue(element)).toBe("");
        expect(element.toJSON()).toBeNull();
    });

    it("serializes an explicitly selected certificate for an existing provider without a signing key", async () => {
        const element = await mountSigningKey({ pk: 1, signingKey: null });

        expect(element.toJSON()).toBeNull();

        element.show();
        await element.updateComplete;

        const option = Array.from(
            element.renderRoot.querySelectorAll<HTMLElement>('[role="option"]'),
        ).find((item) => item.textContent?.includes(certificate.name))!;

        option.click();
        await element.settled;

        expect(element.value).toBe(certificate.pk);
        expect(element.selectedObject).toEqual(certificate);
        expect(inputValue(element)).toBe(certificate.name);
        expect(element.toJSON()).toBe(certificate.pk);
        expect(new FormData(element.closest("form")!).get("signingKey")).toBe(certificate.pk);
    });
});
