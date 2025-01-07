/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { create, Props } from "./utils";

export function createFullWidthTable({ children, style, ...rest }: Props) {
  return create("table", {
    style: { display: "table", width: "100%", ...style },
    ...rest,
    children,
  });
}
