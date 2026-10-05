import { ToggleUserPasswordLockButton } from "#admin/users/UserPasswordLockForm";

import { AuthenticatorsApi, UserFromJSON, UserTypeEnum } from "@goauthentik/api";

import { afterEach, describe, expect, it, vi } from "vitest";
import { page } from "vitest/browser";

import { render } from "lit";

const containers: HTMLElement[] = [];

afterEach(() => {
    for (const container of containers.splice(0)) container.remove();
    vi.restoreAllMocks();
});

function user(locked: boolean, type: UserTypeEnum = UserTypeEnum.Internal) {
    return UserFromJSON({
        pk: 42,
        username: "alice",
        name: "Alice",
        type,
        password_locked: locked,
        password_device: 73,
    });
}

describe("password lock actions", () => {
    it.each([
        [UserTypeEnum.Internal, true, false, "Lock password login"],
        [UserTypeEnum.Internal, false, false, null],
        [UserTypeEnum.Internal, false, true, "Unlock password login"],
        [UserTypeEnum.ServiceAccount, true, false, null],
        [UserTypeEnum.InternalServiceAccount, true, false, null],
        [UserTypeEnum.ServiceAccount, false, true, "Unlock password login"],
    ] as const)(
        "offers the appropriate action for %s, licensed=%s, locked=%s",
        (type, hasEnterpriseLicense, locked, label) => {
            const container = document.createElement("div");
            containers.push(container);
            document.body.append(container);

            render(
                ToggleUserPasswordLockButton(user(locked, type), { hasEnterpriseLicense }),
                container,
            );

            expect(container.querySelector("button")?.textContent.trim() ?? null).toBe(label);
        },
    );

    it("hides lock actions when the user has no password device", () => {
        const container = document.createElement("div");
        const target = user(false);
        target.passwordDevice = null;
        render(ToggleUserPasswordLockButton(target, { hasEnterpriseLicense: true }), container);
        expect(container.querySelector("button")).toBeNull();
    });

    it.each([false, true])("submits the password action for locked=%s", async (locked) => {
        const lock = vi
            .spyOn(AuthenticatorsApi.prototype, "authenticatorsPasswordLockCreate")
            .mockResolvedValue();

        const unlock = vi
            .spyOn(AuthenticatorsApi.prototype, "authenticatorsPasswordUnlockCreate")
            .mockResolvedValue();

        const form = document.createElement("ak-user-password-lock-form");
        form.id = "interface-root";
        form.instance = user(locked);
        const messages = document.createElement("ak-message-container");
        containers.push(messages);
        document.body.append(messages);
        containers.push(form);
        document.body.append(form);

        await page
            .getByRole("button", {
                name: locked ? "Unlock password login" : "Lock password login",
                exact: true,
            })
            .click();

        await expect.poll(() => (locked ? unlock : lock).mock.calls).toEqual([[{ id: 73 }]]);
        expect(locked ? lock : unlock).not.toHaveBeenCalled();

        await expect
            .element(
                page.getByText(locked ? "Password login unlocked" : "Password login locked", {
                    exact: true,
                }),
            )
            .toBeVisible();
    });
});
