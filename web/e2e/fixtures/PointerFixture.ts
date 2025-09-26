import { PageFixture } from "#e2e/fixtures/PageFixture";
import type { LocatorContext } from "#e2e/selectors/types";

import { Page } from "@playwright/test";

export type GetByRoleParameters = Parameters<Page["getByRole"]>;
export type ARIARole = GetByRoleParameters[0];
export type ARIAOptions = GetByRoleParameters[1];

export type ClickByName = (name: string) => Promise<void>;
export type ClickByRole = (
    role: ARIARole,
    options?: ARIAOptions,
    context?: LocatorContext,
) => Promise<void>;

export class PointerFixture extends PageFixture {
    public static fixtureName = "Pointer";

    public click = (
        name: string | RegExp,
        optionsOrRole?: ARIAOptions | ARIARole,
        context: LocatorContext = this.page,
    ): Promise<void> => {
        // TODO: The use of `force: true` is a temporary workaround for
        // buttons with slotted content, which are not considered visible by
        // Playwright. This should be removed after native dialog modals are implemented.

        if (typeof optionsOrRole === "string") {
            return context.getByRole(optionsOrRole, { name }).click({
                force: true,
            });
        }

        const options = {
            ...optionsOrRole,
            name,
        };

        return (
            context
                // ---
                .getByRole("button", options)
                .or(context.getByRole("link", options))
                .click({
                    force: true,
                })
        );
    };
}
