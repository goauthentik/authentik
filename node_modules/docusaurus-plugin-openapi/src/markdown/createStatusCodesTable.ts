/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { createDescription } from "./createDescription";
import { createFullWidthTable } from "./createFullWidthTable";
import { createSchemaTable } from "./createSchemaTable";
import { create } from "./utils";
import { ApiItem } from "../types";

interface Props {
  responses: ApiItem["responses"];
}

export function createStatusCodesTable({ responses }: Props) {
  if (responses === undefined) {
    return undefined;
  }

  const codes = Object.keys(responses);
  if (codes.length === 0) {
    return undefined;
  }

  return createFullWidthTable({
    children: [
      create("thead", {
        children: create("tr", {
          children: create("th", {
            style: { textAlign: "left" },
            children: `Responses`,
          }),
        }),
      }),
      create("tbody", {
        children: codes.map((code) =>
          create("tr", {
            children: create("td", {
              children: [
                create("div", {
                  style: { display: "flex" },
                  children: [
                    create("div", {
                      style: { marginRight: "var(--ifm-table-cell-padding)" },
                      children: create("code", {
                        children: code,
                      }),
                    }),
                    create("div", {
                      children: createDescription(responses[code].description),
                    }),
                  ],
                }),
                create("div", {
                  children: createSchemaTable({
                    style: {
                      marginTop: "var(--ifm-table-cell-padding)",
                      marginBottom: "0px",
                    },
                    title: "Schema",
                    body: {
                      content: responses[code].content,
                    },
                    type: "response",
                  }),
                }),
              ],
            }),
          })
        ),
      }),
    ],
  });
}
