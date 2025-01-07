/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { isURL } from "./util";

describe("util", () => {
  describe("isURL", () => {
    it("full external link", () => {
      const url = "http://www.google.com";
      expect(isURL(url)).toBe(true);
    });

    it("Windows path", () => {
      // this is a windows path checking
      // related to issue #190
      // https://github.com/cloud-annotations/docusaurus-openapi/issues/190
      const url = "C:\\docusaurus-openapi\\openapi.json";
      expect(isURL(url)).toBe(false);
    });

    it("Linux/Unix path", () => {
      const url = "/mnt/c/Users/docusaurus-openapi/openapi.json";
      expect(isURL(url)).toBe(false);
    });
  });
});
