import { sanitizeFilename } from "./file-utils";

import { describe, expect, it } from "vitest";

describe("sanitizeFilename", () => {
    it("removes separators and characters unsafe for headers and Windows filenames", () => {
        for (const name of ["../../foo", "..\\..\\foo", "/foo/bar", "foo\r\nbar\0"]) {
            // eslint-disable-next-line no-control-regex -- Explicitly test the security boundary.
            expect(sanitizeFilename(name)).not.toMatch(/[\\/\x00-\x1f\x7f]/);
        }
    });

    it("supplies a basename when the input has only dots and spaces", () => {
        for (const name of ["", ".", "..", " . "]) {
            expect(sanitizeFilename(name)).toBe("download");
        }
    });

    it("bounds UTF-8 bytes without splitting a Unicode character", () => {
        const filename = sanitizeFilename("😀".repeat(200));
        expect(new TextEncoder().encode(filename).length).toBe(200);
        expect(filename).not.toContain("�");
    });
});
