import { ID_PATTERN, SLUG_PATTERN, UUID_PATTERN } from "./constants.js";

import { describe, expect, it } from "vitest";

describe("router pattern constants", () => {
    it("SLUG_PATTERN matches a slug and rejects a slash", () => {
        const pattern = new URLPattern({ pathname: `/apps/:slug(${SLUG_PATTERN})` });

        expect(pattern.exec({ pathname: "/apps/my-app_1" })?.pathname.groups.slug).toBe("my-app_1");
        expect(pattern.exec({ pathname: "/apps/a/b" })).toBeNull();
    });

    it("ID_PATTERN matches digits only", () => {
        const pattern = new URLPattern({ pathname: `/users/:id(${ID_PATTERN})` });

        expect(pattern.exec({ pathname: "/users/42" })?.pathname.groups.id).toBe("42");
        expect(pattern.exec({ pathname: "/users/abc" })).toBeNull();
    });

    it("UUID_PATTERN matches a uuid", () => {
        const pattern = new URLPattern({ pathname: `/o/:uuid(${UUID_PATTERN})` });
        const uuid = "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d";

        expect(pattern.exec({ pathname: `/o/${uuid}` })?.pathname.groups.uuid).toBe(uuid);
        expect(pattern.exec({ pathname: "/o/not-a-uuid" })).toBeNull();
    });
});
