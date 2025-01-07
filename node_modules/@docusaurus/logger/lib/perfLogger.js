"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PerfLogger = void 0;
const tslib_1 = require("tslib");
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
const async_hooks_1 = require("async_hooks");
const logger_1 = tslib_1.__importDefault(require("./logger"));
// For now this is a private env variable we use internally
// But we'll want to expose this feature officially some day
const PerfDebuggingEnabled = process.env.DOCUSAURUS_PERF_LOGGER === 'true';
const Thresholds = {
    min: 5,
    yellow: 100,
    red: 1000,
};
const PerfPrefix = logger_1.default.yellow(`[PERF]`);
// This is what enables to "see the parent stack" for each log
// Parent1 > Parent2 > Parent3 > child trace
const ParentPrefix = new async_hooks_1.AsyncLocalStorage();
function applyParentPrefix(label) {
    const parentPrefix = ParentPrefix.getStore();
    return parentPrefix ? `${parentPrefix} > ${label}` : label;
}
function getMemory() {
    // Before reading memory stats, we explicitly call the GC
    // Note: this only works when Node.js option "--expose-gc" is provided
    globalThis.gc?.();
    return process.memoryUsage();
}
function createPerfLogger() {
    if (!PerfDebuggingEnabled) {
        const noop = () => { };
        return {
            start: noop,
            end: noop,
            log: noop,
            async: async (_label, asyncFn) => asyncFn(),
        };
    }
    const formatDuration = (duration) => {
        if (duration > Thresholds.red) {
            return logger_1.default.red(`${(duration / 1000).toFixed(2)} seconds!`);
        }
        else if (duration > Thresholds.yellow) {
            return logger_1.default.yellow(`${duration.toFixed(2)} ms`);
        }
        else {
            return logger_1.default.green(`${duration.toFixed(2)} ms`);
        }
    };
    const formatMemory = (memory) => {
        const fmtHead = (bytes) => logger_1.default.cyan(`${(bytes / 1000000).toFixed(0)}mb`);
        return logger_1.default.dim(`(${fmtHead(memory.before.heapUsed)} -> ${fmtHead(memory.after.heapUsed)})`);
    };
    const formatStatus = (error) => {
        return error ? logger_1.default.red('[KO]') : ''; // logger.green('[OK]');
    };
    const printPerfLog = ({ label, duration, memory, error, }) => {
        if (duration < Thresholds.min) {
            return;
        }
        console.log(`${PerfPrefix}${formatStatus(error)} ${label} - ${formatDuration(duration)} - ${formatMemory(memory)}`);
    };
    const start = (label) => performance.mark(label, {
        detail: {
            memoryUsage: getMemory(),
        },
    });
    const end = (label) => {
        const { duration, detail: { memoryUsage }, } = performance.measure(label);
        performance.clearMarks(label);
        printPerfLog({
            label: applyParentPrefix(label),
            duration,
            memory: {
                before: memoryUsage,
                after: getMemory(),
            },
            error: undefined,
        });
    };
    const log = (label) => console.log(`${PerfPrefix} ${applyParentPrefix(label)}`);
    const async = async (label, asyncFn) => {
        const finalLabel = applyParentPrefix(label);
        const before = performance.now();
        const memoryBefore = getMemory();
        const asyncEnd = ({ error }) => {
            const memoryAfter = getMemory();
            const duration = performance.now() - before;
            printPerfLog({
                error,
                label: finalLabel,
                duration,
                memory: {
                    before: memoryBefore,
                    after: memoryAfter,
                },
            });
        };
        try {
            const result = await ParentPrefix.run(finalLabel, () => asyncFn());
            asyncEnd({ error: undefined });
            return result;
        }
        catch (e) {
            asyncEnd({ error: e });
            throw e;
        }
    };
    return {
        start,
        end,
        log,
        async,
    };
}
exports.PerfLogger = createPerfLogger();
//# sourceMappingURL=perfLogger.js.map