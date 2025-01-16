"use strict";
/* ============================================================================
 * Copyright (c) Palo Alto Networks
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
const CodeSnippets_1 = __importDefault(
  require("@theme/ApiExplorer/CodeSnippets")
);
const Request_1 = __importDefault(require("@theme/ApiExplorer/Request"));
const Response_1 = __importDefault(require("@theme/ApiExplorer/Response"));
const SecuritySchemes_1 = __importDefault(
  require("@theme/ApiExplorer/SecuritySchemes")
);
const postman_collection_1 = __importDefault(require("postman-collection"));
function ApiExplorer({ item, infoPath }) {
  const postman = new postman_collection_1.default.Request(item.postman);
  return react_1.default.createElement(
    react_1.default.Fragment,
    null,
    react_1.default.createElement(SecuritySchemes_1.default, {
      infoPath: infoPath,
    }),
    item.method !== "event" &&
      react_1.default.createElement(CodeSnippets_1.default, {
        postman: postman,
        codeSamples: item["x-codeSamples"] ?? [],
      }),
    react_1.default.createElement(Request_1.default, { item: item }),
    react_1.default.createElement(Response_1.default, { item: item })
  );
}
exports.default = ApiExplorer;
