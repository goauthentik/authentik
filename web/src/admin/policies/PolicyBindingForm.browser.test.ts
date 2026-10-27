import { PolicyBindingCheckTarget } from "#common/policies/utils";

import { DeviceUserBindingForm } from "#admin/endpoints/devices/DeviceUserBindingForm";
import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";

import {
    CoreApi,
    type DeviceUserBinding,
    EndpointsApi,
    PoliciesApi,
    type PolicyBinding,
} from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

beforeEach(() => {
    // Keep subject selection and order loading local while exercising the real form.
    const empty = {
        results: [],
        autocomplete: {},
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

    vi.spyOn(PoliciesApi.prototype, "policiesBindingsList").mockResolvedValue(empty);
    vi.spyOn(PoliciesApi.prototype, "policiesAllList").mockResolvedValue(empty);
    vi.spyOn(CoreApi.prototype, "coreGroupsList").mockResolvedValue(empty);
    vi.spyOn(CoreApi.prototype, "coreUsersList").mockResolvedValue(empty);
});

afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
});

async function mount(instance: PolicyBinding | null = null) {
    const form = new PolicyBindingForm();
    form.instance = instance;
    form.targetPk = "target";
    document.body.append(form);
    await form.updateComplete;

    await expect
        .poll(() => form.renderRoot.querySelector('ak-switch-input[name="dryRun"]'))
        .not.toBeNull();

    const control = form.renderRoot.querySelector<HTMLElementTagNameMap["ak-switch-input"]>(
        'ak-switch-input[name="dryRun"]',
    );

    if (!control) throw new Error("Dry-run switch did not render");
    await control.updateComplete;

    return { form, checkbox: control.checkbox };
}

describe("PolicyBindingForm", () => {
    it.each([false, true])(
        "omits dry-run controls and values for device bindings (existing: %s)",
        async (existing) => {
            const create = vi
                .spyOn(EndpointsApi.prototype, "endpointsDeviceBindingsCreate")
                .mockResolvedValue({} as DeviceUserBinding);

            const update = vi
                .spyOn(EndpointsApi.prototype, "endpointsDeviceBindingsUpdate")
                .mockResolvedValue({} as DeviceUserBinding);

            const form = new DeviceUserBindingForm();
            form.targetPk = "device";
            form.allowedTypes = [PolicyBindingCheckTarget.User];

            form.instance = existing
                ? ({ pk: "binding", dryRun: true } as DeviceUserBinding)
                : null;

            document.body.append(form);
            await form.updateComplete;

            await expect
                .poll(() => form.renderRoot.querySelector('ak-switch-input[name="enabled"]'))
                .not.toBeNull();

            const enabled = form.renderRoot.querySelector<HTMLElementTagNameMap["ak-switch-input"]>(
                'ak-switch-input[name="enabled"]',
            );

            expect(enabled).not.toBeNull();
            await enabled!.updateComplete;

            expect(form.renderRoot.querySelector('[name="dryRun"]')).toBeNull();
            expect(form.toJSON()).not.toHaveProperty("dryRun");
            await form.send({ ...form.toJSON(), user: 1 });

            const request = existing
                ? update.mock.calls[0][0].deviceUserBindingRequest
                : create.mock.calls[0][0].deviceUserBindingRequest;

            expect(request).toMatchObject({ target: "device", user: 1 });
            expect(request).not.toHaveProperty("dryRun");
        },
    );

    it.each([PolicyBindingCheckTarget.User, PolicyBindingCheckTarget.Group])(
        "offers and preserves dry-run for a %s binding",
        async (target) => {
            const create = vi
                .spyOn(PoliciesApi.prototype, "policiesBindingsCreate")
                .mockResolvedValue({} as PolicyBinding);

            const { form, checkbox } = await mount();
            form.policyGroupUser = target;
            await form.updateComplete;

            expect(
                form.renderRoot.querySelector<HTMLElement>('ak-switch-input[name="dryRun"]')
                    ?.hidden,
            ).toBe(false);

            checkbox.click();
            await form.send({ ...form.toJSON(), user: 1, group: "group" });

            expect(create).toHaveBeenCalledWith({
                policyBindingRequest: expect.objectContaining({ dryRun: true, policy: null }),
            });
        },
    );

    it("defaults to enforcement and sends an explicitly enabled dry-run on creation", async () => {
        const create = vi
            .spyOn(PoliciesApi.prototype, "policiesBindingsCreate")
            .mockResolvedValue({} as PolicyBinding);

        const { form, checkbox } = await mount();

        expect(checkbox.checked).toBe(false);
        checkbox.click();
        await form.send(form.toJSON());

        expect(create).toHaveBeenCalledWith({
            policyBindingRequest: expect.objectContaining({ target: "target", dryRun: true }),
        });
    });

    it("loads an existing dry-run and sends false when enforcement is restored", async () => {
        const update = vi
            .spyOn(PoliciesApi.prototype, "policiesBindingsUpdate")
            .mockResolvedValue({} as PolicyBinding);

        const { form, checkbox } = await mount({ pk: "binding", dryRun: true } as PolicyBinding);

        expect(checkbox.checked).toBe(true);
        checkbox.click();
        await form.send(form.toJSON());

        expect(update).toHaveBeenCalledWith({
            policyBindingUuid: "binding",
            policyBindingRequest: expect.objectContaining({ dryRun: false }),
        });
    });
});
