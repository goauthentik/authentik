"use strict";
/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const path_1 = __importDefault(require("path"));
const _1 = require(".");
// npx jest packages/docusaurus-plugin-openapi/src/openapi/openapi.test.ts --watch
describe("openapi", () => {
    describe("readOpenapiFiles", () => {
        it("readOpenapiFiles", async () => {
            const results = await (0, _1.readOpenapiFiles)(path_1.default.join(__dirname, "__fixtures__/examples"), {});
            const categoryMeta = results.find((x) => x.source.endsWith("_category_.json"));
            expect(categoryMeta).toBeFalsy();
            // console.log(results);
            const yaml = results.find((x) => x.source.endsWith("openapi.yaml"));
            expect(yaml).toBeTruthy();
            expect(yaml === null || yaml === void 0 ? void 0 : yaml.sourceDirName).toBe(".");
            const froyo = results.find((x) => x.source.endsWith("froyo.yaml"));
            expect(froyo).toBeTruthy();
            expect(froyo === null || froyo === void 0 ? void 0 : froyo.sourceDirName).toBe("yogurtstore");
            const nested = results.find((x) => x.source.endsWith("nested.yaml"));
            expect(nested).toBeTruthy();
            expect(nested === null || nested === void 0 ? void 0 : nested.sourceDirName).toBe("yogurtstore/nested");
        });
    });
});
