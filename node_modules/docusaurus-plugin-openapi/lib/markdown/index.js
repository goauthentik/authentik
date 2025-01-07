"use strict";
/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createInfoPageMD = exports.createApiPageMD = void 0;
const lodash_1 = require("lodash");
const createDeprecationNotice_1 = require("./createDeprecationNotice");
const createDescription_1 = require("./createDescription");
const createParamsTable_1 = require("./createParamsTable");
const createRequestBodyTable_1 = require("./createRequestBodyTable");
const createStatusCodesTable_1 = require("./createStatusCodesTable");
const createVersionBadge_1 = require("./createVersionBadge");
const utils_1 = require("./utils");
function createApiPageMD({ title, api: { deprecated, "x-deprecated-description": deprecatedDescription, description, parameters, requestBody, responses, }, }) {
    return (0, utils_1.render)([
        `# ${(0, lodash_1.escape)(title)}\n\n`,
        (0, createDeprecationNotice_1.createDeprecationNotice)({ deprecated, description: deprecatedDescription }),
        (0, createDescription_1.createDescription)(description),
        (0, createParamsTable_1.createParamsTable)({ parameters, type: "path" }),
        (0, createParamsTable_1.createParamsTable)({ parameters, type: "query" }),
        (0, createParamsTable_1.createParamsTable)({ parameters, type: "header" }),
        (0, createParamsTable_1.createParamsTable)({ parameters, type: "cookie" }),
        (0, createRequestBodyTable_1.createRequestBodyTable)({ title: "Request Body", body: requestBody }),
        (0, createStatusCodesTable_1.createStatusCodesTable)({ responses }),
    ]);
}
exports.createApiPageMD = createApiPageMD;
function createInfoPageMD({ info: { title, version, description }, }) {
    return (0, utils_1.render)([
        (0, createVersionBadge_1.createVersionBadge)(version),
        `# ${(0, lodash_1.escape)(title)}\n\n`,
        (0, createDescription_1.createDescription)(description),
    ]);
}
exports.createInfoPageMD = createInfoPageMD;
