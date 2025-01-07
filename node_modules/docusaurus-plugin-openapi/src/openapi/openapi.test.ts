/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import path from "path";

import { readOpenapiFiles } from ".";

// npx jest packages/docusaurus-plugin-openapi/src/openapi/openapi.test.ts --watch

describe("openapi", () => {
  describe("readOpenapiFiles", () => {
    it("readOpenapiFiles", async () => {
      const results = await readOpenapiFiles(
        path.join(__dirname, "__fixtures__/examples"),
        {}
      );
      const categoryMeta = results.find((x) =>
        x.source.endsWith("_category_.json")
      );
      expect(categoryMeta).toBeFalsy();
      // console.log(results);
      const yaml = results.find((x) => x.source.endsWith("openapi.yaml"));
      expect(yaml).toBeTruthy();
      expect(yaml?.sourceDirName).toBe(".");
      const froyo = results.find((x) => x.source.endsWith("froyo.yaml"));
      expect(froyo).toBeTruthy();
      expect(froyo?.sourceDirName).toBe("yogurtstore");
      const nested = results.find((x) => x.source.endsWith("nested.yaml"));
      expect(nested).toBeTruthy();
      expect(nested?.sourceDirName).toBe("yogurtstore/nested");
    });
  });
});
