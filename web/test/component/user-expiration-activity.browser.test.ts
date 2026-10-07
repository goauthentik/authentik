import "#admin/lifecycle/UserExpirationRuleForm";
import { serializeForm } from "#elements/forms/serialization";
import type { SlottedTemplateResult } from "#elements/types";

import type { AkRadioInput } from "#components/ak-radio-input";

import {
    ActivityBasisEnum,
    type UserExpirationRule,
    UserExpirationRuleFromJSON,
} from "@goauthentik/api";

import { afterEach, expect, test, vi } from "vitest";

import { render } from "lit";

const api = vi.hoisted(() => ({
    lifecycleUserExpirationRulesCreate: vi.fn().mockResolvedValue({}),
    lifecycleUserExpirationRulesUpdate: vi.fn().mockResolvedValue({}),
}));

// These component tests exercise form rendering and submission without a server.
vi.mock("#common/api/client", () => ({ aki: () => api }));

type FormAccess = {
    renderForm(): SlottedTemplateResult;
    send(data: UserExpirationRule): Promise<UserExpirationRule>;
};

const mounted: HTMLElement[] = [];

afterEach(() => {
    for (const element of mounted.splice(0)) element.remove();
    vi.clearAllMocks();
});

async function activityField(instance?: UserExpirationRule) {
    const form = document.createElement("ak-user-expiration-rule-form");
    form.instance = instance ?? null;
    const access = form as unknown as FormAccess;
    const container = document.createElement("div");
    render(access.renderForm(), container);

    const field = container.querySelector<AkRadioInput<ActivityBasisEnum>>(
        'ak-radio-input[name="activityBasis"]',
    )!;

    // Mount only this field; unrelated group/transport selectors need API fixtures.
    document.body.append(field);
    mounted.push(field);
    await field.updateComplete;
    await field.querySelector("ak-radio")!.updateComplete;

    return { form, access, field };
}

test("defaults new rules to Last activity and explains retention and sampling", async () => {
    const { field } = await activityField();
    expect(field.value).toBe(ActivityBasisEnum.SuccessfulEvents);
    expect(field.help).toContain("365 days");
    expect(field.help).toContain("duration plus 24 hours");
    const text = field.querySelector("ak-radio")!.shadowRoot!.textContent;
    expect(text).toContain("24-hour allowance");
    expect(text).toContain("API-token requests do not count");
});

test("keeps the saved activity basis when editing", async () => {
    const { field } = await activityField(
        UserExpirationRuleFromJSON({
            pk: "00000000-0000-0000-0000-000000000001",
            name: "Login rule",
            activity_basis: ActivityBasisEnum.LastLogin,
        }),
    );

    expect(field.value).toBe(ActivityBasisEnum.LastLogin);
});

test("serializes the selected activity basis and submits it through the client", async () => {
    const { access, field } = await activityField();

    field
        .querySelector("ak-radio")!
        .shadowRoot!.querySelector<HTMLInputElement>('input[aria-label="Last login"]')!
        .click();

    await field.updateComplete;
    const data = serializeForm<UserExpirationRule>([field]);
    expect(data.activityBasis).toBe(ActivityBasisEnum.LastLogin);

    await access.send(
        UserExpirationRuleFromJSON({
            activity_basis: data.activityBasis,
            name: "Login rule",
        }),
    );

    expect(api.lifecycleUserExpirationRulesCreate).toHaveBeenCalledWith({
        userExpirationRuleRequest: expect.objectContaining({
            name: "Login rule",
            activityBasis: ActivityBasisEnum.LastLogin,
            group: null,
            warnBefore: null,
        }),
    });
});
