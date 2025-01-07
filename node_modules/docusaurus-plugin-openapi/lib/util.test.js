"use strict";
/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
Object.defineProperty(exports, "__esModule", { value: true });
const util_1 = require("./util");
describe("util", () => {
    describe("isURL", () => {
        it("full external link", () => {
            const url = "http://www.google.com";
            expect((0, util_1.isURL)(url)).toBe(true);
        });
        it("Windows path", () => {
            // this is a windows path checking
            // related to issue #190
            // https://github.com/cloud-annotations/docusaurus-openapi/issues/190
            const url = "C:\\docusaurus-openapi\\openapi.json";
            expect((0, util_1.isURL)(url)).toBe(false);
        });
        it("Linux/Unix path", () => {
            const url = "/mnt/c/Users/docusaurus-openapi/openapi.json";
            expect((0, util_1.isURL)(url)).toBe(false);
        });
    });
});
