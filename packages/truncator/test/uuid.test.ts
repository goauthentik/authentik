import { truncateUUID } from "../src/uuid.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

describe("truncateUUID", () => {
    const uuid = "550e8400-e29b-41d4-a716-446655440000";

    it("returns the uuid unchanged when it fits", () => {
        expect(truncateUUID(uuid, cc(40))).toBe(uuid);
    });

    it("drops middle segments keeping first and last", () => {
        expect(truncateUUID(uuid, cc(25))).toBe("550e8400-…-446655440000");
    });

    it("never exceeds the budget", () => {
        expect(truncateUUID(uuid, cc(12)).length).toBeLessThanOrEqual(12);
    });
});
