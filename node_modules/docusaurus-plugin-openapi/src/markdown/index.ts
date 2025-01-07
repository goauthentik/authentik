/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { escape } from "lodash";

import { createDeprecationNotice } from "./createDeprecationNotice";
import { createDescription } from "./createDescription";
import { createParamsTable } from "./createParamsTable";
import { createRequestBodyTable } from "./createRequestBodyTable";
import { createStatusCodesTable } from "./createStatusCodesTable";
import { createVersionBadge } from "./createVersionBadge";
import { render } from "./utils";
import { ApiPageMetadata, InfoPageMetadata } from "../types";

export function createApiPageMD({
  title,
  api: {
    deprecated,
    "x-deprecated-description": deprecatedDescription,
    description,
    parameters,
    requestBody,
    responses,
  },
}: ApiPageMetadata) {
  return render([
    `# ${escape(title)}\n\n`,
    createDeprecationNotice({ deprecated, description: deprecatedDescription }),
    createDescription(description),
    createParamsTable({ parameters, type: "path" }),
    createParamsTable({ parameters, type: "query" }),
    createParamsTable({ parameters, type: "header" }),
    createParamsTable({ parameters, type: "cookie" }),
    createRequestBodyTable({ title: "Request Body", body: requestBody }),
    createStatusCodesTable({ responses }),
  ]);
}

export function createInfoPageMD({
  info: { title, version, description },
}: InfoPageMetadata) {
  return render([
    createVersionBadge(version),
    `# ${escape(title)}\n\n`,
    createDescription(description),
  ]);
}
