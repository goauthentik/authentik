import { pageBounds, paginatedBounds } from "./bounds";
import { Pagination } from "./Paginator";

import { describe, expect, it } from "vitest";

describe("pageBounds", () => {
    it("finds the first page in a large collection correctly", () => {
        expect(pageBounds(471, 20, 1)).toStrictEqual({
            page: 1,
            totalPages: 24,
            startIndex: 1,
            endIndex: 20,
        });
    });

    it("finds a middle page in a large collection correctly", () => {
        expect(pageBounds(471, 20, 3)).toStrictEqual({
            page: 3,
            totalPages: 24,
            startIndex: 41,
            endIndex: 60,
        });
    });

    it("doesn't exceed the item count on the last page", () => {
        expect(pageBounds(471, 20, 24)).toStrictEqual({
            page: 24,
            totalPages: 24,
            startIndex: 461,
            endIndex: 471,
        });
    });

    it("gives you page 1 and no items when there are no items", () => {
        expect(pageBounds(0, 20, 1)).toStrictEqual({
            page: 1,
            totalPages: 0,
            startIndex: 0,
            endIndex: 0,
        });
    });

    it("gives you page 1 of 1 pages and the endIndex equals item count when there are less than itemsPerPage items", () => {
        expect(pageBounds(7, 20, 1)).toStrictEqual({
            page: 1,
            totalPages: 1,
            startIndex: 1,
            endIndex: 7,
        });
    });

    it("won't accept page numbers beyond the final page", () => {
        expect(pageBounds(50, 20, 7).page).toBe(3);
    });

    it("Won't accept page numbers less than one", () => {
        expect(pageBounds(50, 20, 0).page).toBe(1);
        expect(pageBounds(50, 20, -3).page).toBe(1);
    });

    it("handles itemsPerPage less than one as one", () => {
        expect(pageBounds(5, 0, 1)).toStrictEqual({
            page: 1,
            totalPages: 5,
            startIndex: 1,
            endIndex: 1,
        });

        expect(pageBounds(5, -5, 1)).toStrictEqual({
            page: 1,
            totalPages: 5,
            startIndex: 1,
            endIndex: 1,
        });
    });

    it("handles NaN", () => {
        expect(pageBounds(Number.NaN, Number.NaN, Number.NaN)).toStrictEqual({
            page: 1,
            totalPages: 0,
            startIndex: 0,
            endIndex: 0,
        });
    });
});

function fakeDjangoPagination(overrides: Partial<Pagination>): Pagination {
    return {
        next: 0,
        previous: 0,
        count: 0,
        current: 1,
        totalPages: 0,
        startIndex: 0,
        endIndex: 0,
        ...overrides,
    };
}

describe("paginationCalc", () => {
    it("finds the middle page as sent by Django", () => {
        expect(
            paginatedBounds(
                fakeDjangoPagination({
                    count: 471,
                    current: 3,
                    totalPages: 24,
                    startIndex: 41,
                    endIndex: 60,
                }),
            ),
        ).toStrictEqual({
            page: 3,
            totalPages: 24,
            startIndex: 41,
            endIndex: 60,
        });
    });
});
