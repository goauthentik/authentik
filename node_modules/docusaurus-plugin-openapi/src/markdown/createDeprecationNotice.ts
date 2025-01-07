/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { guard, Props, render } from "./utils";

function createAdmonition({ children }: Props) {
  return `:::caution[deprecated]\n\n${render(children)}\n\n:::`;
}

interface DeprecationNoticeProps {
  deprecated?: boolean;
  description?: string;
}

export function createDeprecationNotice({
  deprecated,
  description,
}: DeprecationNoticeProps) {
  return guard(deprecated, () =>
    createAdmonition({
      children:
        description ??
        "This endpoint has been deprecated and may be removed in future versions of the API.",
    })
  );
}
