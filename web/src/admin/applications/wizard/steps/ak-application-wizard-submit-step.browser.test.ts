import { ApplicationWizardSubmitStep } from "#admin/applications/wizard/steps/ak-application-wizard-submit-step";

import {
    type Application,
    CoreApi,
    PoliciesApi,
    type PolicyBinding,
    ProvidersApi,
    ProxyMode,
    type SAMLProvider,
    type TransactionApplicationResponse,
} from "@goauthentik/api";

import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => vi.restoreAllMocks());

function step(dryRun: boolean, providerModel: string) {
    const element = new ApplicationWizardSubmitStep();

    element.wizard = {
        app: { name: "Dry-run test", slug: "dry-run-test" },
        providerModel,
        provider: {},
        proxyMode: ProxyMode.Proxy,
        bindings: [{ policy: "policy", order: 0, dryRun } as PolicyBinding],
        currentBinding: -1,
        errors: {},
    };

    return element;
}

describe("ApplicationWizardSubmitStep", () => {
    it.each([true, false])("preserves dryRun=%s in the application transaction", async (dryRun) => {
        const submit = vi
            .spyOn(CoreApi.prototype, "coreTransactionalApplicationsUpdate")
            .mockResolvedValue({} as TransactionApplicationResponse);

        await step(dryRun, "oauth2provider").send();

        expect(submit).toHaveBeenCalledWith({
            transactionApplicationRequest: expect.objectContaining({
                policyBindings: [expect.objectContaining({ policy: "policy", dryRun })],
            }),
        });
    });

    it.each([true, false])("preserves dryRun=%s when importing SAML metadata", async (dryRun) => {
        vi.spyOn(ProvidersApi.prototype, "providersSamlImportMetadataCreate").mockResolvedValue({
            pk: 1,
        } as SAMLProvider);

        vi.spyOn(CoreApi.prototype, "coreApplicationsCreate").mockResolvedValue({
            pk: "application",
        } as Application);

        const createBinding = vi
            .spyOn(PoliciesApi.prototype, "policiesBindingsCreate")
            .mockResolvedValue({} as PolicyBinding);

        await step(dryRun, "samlproviderimportmodel").send();

        expect(createBinding).toHaveBeenCalledWith({
            policyBindingRequest: expect.objectContaining({
                target: "application",
                policy: "policy",
                dryRun,
            }),
        });
    });
});
