var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
import { readFileSync } from "fs";
import path from "path";
import pseudolocale from "pseudolocale";
import { fileURLToPath } from "url";
import { makeFormatter } from "@lit/localize-tools/lib/formatters/index.js";
import { sortProgramMessages } from "@lit/localize-tools/lib/messages.js";
import { TransformLitLocalizer } from "@lit/localize-tools/lib/modes/transform.js";
var __dirname = fileURLToPath(new URL(".", import.meta.url));
var pseudoLocale = "pseudo-LOCALE";
var targetLocales = [pseudoLocale];
var baseConfig = JSON.parse(readFileSync(path.join(__dirname, "../lit-localize.json"), "utf-8"));
// Need to make some internal specifications to satisfy the transformer. It doesn't actually matter
// which Localizer we use (transformer or runtime), because all of the functionality we care about
// is in their common parent class, but I had to pick one.  Everything else here is just pure
// exploitation of the lit/localize-tools internals.
var config = __assign(__assign({}, baseConfig), { baseDir: path.join(__dirname, ".."), targetLocales: targetLocales, output: __assign(__assign({}, baseConfig), { mode: "transform" }), resolve: function (path) { return path; } });
var pseudoMessagify = function (message) { return ({
    name: message.name,
    contents: message.contents.map(function (content) {
        return typeof content === "string" ? pseudolocale(content, { prepend: "", append: "" }) : content;
    }),
}); };
var localizer = new TransformLitLocalizer(config);
var messages = localizer.extractSourceMessages().messages;
var translations = messages.map(pseudoMessagify);
var sorted = sortProgramMessages(__spreadArray([], messages, true));
var formatter = makeFormatter(config);
formatter.writeOutput(sorted, new Map([[pseudoLocale, translations]]));
