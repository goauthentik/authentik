"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.reportUnresolvedRef = exports.NoUnresolvedRefs = void 0;
const resolve_1 = require("../resolve");
const NoUnresolvedRefs = () => {
    return {
        ref: {
            leave(_, { report, location }, resolved) {
                if (resolved.node !== undefined)
                    return;
                reportUnresolvedRef(resolved, report, location);
            },
        },
        DiscriminatorMapping(mapping, { report, resolve, location }) {
            for (const mappingName of Object.keys(mapping)) {
                const resolved = resolve({ $ref: mapping[mappingName] });
                if (resolved.node !== undefined)
                    return;
                reportUnresolvedRef(resolved, report, location.child(mappingName));
            }
        },
    };
};
exports.NoUnresolvedRefs = NoUnresolvedRefs;
function reportUnresolvedRef(resolved, report, location) {
    var _a;
    const error = resolved.error;
    if (error instanceof resolve_1.YamlParseError) {
        report({
            message: 'Failed to parse: ' + error.message,
            location: {
                source: error.source,
                pointer: undefined,
                start: {
                    col: error.col,
                    line: error.line,
                },
            },
        });
    }
    const message = (_a = resolved.error) === null || _a === void 0 ? void 0 : _a.message;
    report({
        location,
        message: `Can't resolve $ref${message ? ': ' + message : ''}`,
    });
}
exports.reportUnresolvedRef = reportUnresolvedRef;
