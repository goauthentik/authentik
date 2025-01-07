/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { escape } from "lodash";

import { create, guard } from "./utils";

export function createVersionBadge(version: string | undefined) {
  return guard(version, (version) => [
    create("span", {
      className: "theme-doc-version-badge badge badge--secondary",
      children: `Version: ${escape(version)}`,
    }),
    `\n`,
  ]);
}
