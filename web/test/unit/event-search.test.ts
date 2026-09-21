import { eventUuidSearch } from "#admin/events/eventSearch";

import { describe, expect, it } from "vitest";

describe("eventUuidSearch", () => {
    it("builds an equality query for a single uuid", () => {
        expect(eventUuidSearch(["a-1"])).toBe('event_uuid = "a-1"');
    });

    it("builds an in-list query for several uuids", () => {
        expect(eventUuidSearch(["a-1", "b-2"])).toBe('event_uuid in ("a-1", "b-2")');
    });

    it("returns an empty query for no uuids", () => {
        expect(eventUuidSearch([])).toBe("");
    });
});
