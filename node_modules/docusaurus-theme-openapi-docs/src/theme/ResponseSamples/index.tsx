/* ============================================================================
 * Copyright (c) Palo Alto Networks
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import React from "react";

import CodeBlock from "@theme/CodeBlock";
import { Language } from "prism-react-renderer";

export interface Props {
  readonly responseExample: string;
  readonly language: Language;
}

function ResponseSamples({
  responseExample,
  language,
}: Props): React.JSX.Element {
  return (
    <div className="openapi-code__response-samples-container">
      <CodeBlock language={language ? language : "json"}>
        {responseExample}
      </CodeBlock>
    </div>
  );
}

export default ResponseSamples;
