/**
 * @file Simplified Flow Executor (SFE) entry point.
 */
import "formdata-polyfill";
import $ from "jquery";

import { SimpleFlowExecutor } from "./lib/index.js";

const flowContainer = /** @type {HTMLDivElement} */ ($("#flow-sfe-container")[0]);

if (!flowContainer) {
    throw new Error("No flow container element found");
}

const sfe = new SimpleFlowExecutor(flowContainer);

sfe.start();
