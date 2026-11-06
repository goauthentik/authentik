import { BoundPoliciesList } from "#admin/policies/BoundPoliciesList";

import { type PolicyBinding } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

import { render } from "lit";

describe("BoundPoliciesList", () => {
    it.each([{ user: 1 }, { group: "group" }, { policy: "policy" }])(
        "links dry-run results using the serialized binding key for %j",
        (subject) => {
            const list = new BoundPoliciesList();
            const container = document.createElement("div");

            const binding = {
                pk: "12345678-1234-5678-1234-567812345678",
                dryRun: true,
                order: 0,
                ...subject,
            } as PolicyBinding;

            render(list.row(binding).at(-1), container);
            const link = container.querySelector("a");
            expect(link).not.toBeNull();
            const href = decodeURIComponent(link!.href);
            expect(href).toContain("context.binding.pk");
            expect(href).toContain("12345678123456781234567812345678");
            expect(href).not.toContain("policy_binding_uuid");
        },
    );
});
