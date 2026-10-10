import { createPaginatedResponse } from "#common/api/responses";

import {
    USER_ATTRIBUTE_REQUIRED_ACTIONS,
    UserRequiredActionsList,
} from "#admin/users/UserRequiredActionsList";

import { CoreApi, Flow, FlowFromJSON, FlowsApi, UserFromJSON } from "@goauthentik/api";

import { afterEach, describe, expect, it, vi } from "vitest";

class TestRequiredActionsList extends UserRequiredActionsList {
    public loadActions() {
        return this.apiEndpoint();
    }

    public addAction(flow: Flow) {
        this.selectedFlow = flow;

        return this.addSelected();
    }
}

customElements.define("ak-test-required-actions-list", TestRequiredActionsList);

afterEach(() => vi.restoreAllMocks());

describe("User required actions", () => {
    it("refreshes actions completed since the user page loaded", async () => {
        const flow = FlowFromJSON({ slug: "setup", name: "Set up authenticator" });

        const user = UserFromJSON({
            pk: 1,
            attributes: { [USER_ATTRIBUTE_REQUIRED_ACTIONS]: [flow.slug] },
        });

        const retrieve = vi.spyOn(CoreApi.prototype, "coreUsersRetrieve").mockResolvedValue(user);

        vi.spyOn(FlowsApi.prototype, "flowsInstancesList").mockResolvedValue(
            createPaginatedResponse([flow]),
        );

        const list = new TestRequiredActionsList();
        list.user = user;

        expect((await list.loadActions()).results).toEqual([flow]);

        retrieve.mockResolvedValue(UserFromJSON({ pk: 1, attributes: {} }));
        expect((await list.loadActions()).results).toEqual([]);
    });

    it("preserves current attributes and avoids adding a flow twice", async () => {
        const flow = FlowFromJSON({ slug: "setup" });
        const user = UserFromJSON({ pk: 1, attributes: {} });

        const attributes = {
            department: "Support",
            [USER_ATTRIBUTE_REQUIRED_ACTIONS]: [flow.slug],
        };

        vi.spyOn(CoreApi.prototype, "coreUsersRetrieve").mockResolvedValue({ ...user, attributes });

        const update = vi
            .spyOn(CoreApi.prototype, "coreUsersPartialUpdate")
            .mockResolvedValue({ ...user, attributes });

        const list = new TestRequiredActionsList();
        list.user = user;

        await list.addAction(flow);

        expect(update).toHaveBeenCalledExactlyOnceWith({
            id: user.pk,
            patchedUserRequest: { attributes },
        });
    });
});
