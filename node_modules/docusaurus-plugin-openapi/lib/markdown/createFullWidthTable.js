"use strict";
/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createFullWidthTable = void 0;
const utils_1 = require("./utils");
function createFullWidthTable({ children, style, ...rest }) {
    return (0, utils_1.create)("table", {
        style: { display: "table", width: "100%", ...style },
        ...rest,
        children,
    });
}
exports.createFullWidthTable = createFullWidthTable;
