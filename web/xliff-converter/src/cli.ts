import { Command } from "commander";
import { XMLParser, XMLBuilder } from "fast-xml-parser";
import { readFileSync } from "fs";
import PO from "pofile";
import specialCases from "./specialCases";

const packageJson = require("../package.json");
const version: string = packageJson.version;

const program = new Command();

program
    .version(version)
    .name("po2xliff")
    .option("-d, --debug", "enables verbose logging", false)
    .option("-x, --xml <filename>", "xliff file to amend", false)
    .option("-p, --po <filename>", "po file as source", false)
    .parse(process.argv);

const options = {
    ignoreAttributes: false,
    preserveOrder: true,
    alwaysCreateTextNode: true,
    trimValues: false,
};

// This translates the text found in a <source> entry into the PO msgid, but always uses positional
// markers for string substitution. See the file `specialCases.ts` for comments on how to identify
// named markers, and what to do if you have any.

function sourceToMsgid(source: any) {
    const key = source["source"].reduce((acc: string, node: any) => {
        if (typeof node["#text"] !== "undefined") {
            return acc + node["#text"];
        }
        if (typeof node["x"] !== "undefined") {
            return acc + "{" + node[":@"]["@_id"] + "}";
        }
        throw new Error("Unrecognized node in source:" + JSON.stringify(node, null, 20));
    }, "");

    return key.replace(/\s+/gms, " ");
}

// Takes a `<source>` object and, for every node in the source object that is an `<x>` template
// object replacement, create a map from the `<x>` object's keys to the object itself. The resulting
// map can be used to create the target string.

function sourceToXMap(source: any): Map<string, any> {
    return source["source"].reduce((acc: Map<string, any>, node: any) => {
        if (typeof node["x"] === "undefined") {
            return acc;
        }
        const attrs = node[":@"];
        if (typeof attrs === "undefined") {
            throw new Error("X with no attributes?");
        }
        acc.set(attrs["@_id"], node);
        acc.set(attrs["@_equiv-text"].replace(/[\$}{\s]/g, ""), node);
        return acc;
    }, new Map());
}

// Given a PO `msgstr` and the `<source>` node, we can generate a map from all the template keys
// used in the `msgstr` to their XLIFF equivalents. By splitting the `msgstr` between the `{...}`
// and preserving the `{...}` entries, we can create a new `<target>` object where the elements are,
// like `<source>` nodes, either parts of the original PO msgstr's text, or the XLIFF equivalent
// substitution nodes. Returns the `<target>` node as a JSON object.

function poToMappedSource(msgstr: string, source: any) {
    // Keys and values for THIS source item, mapped.  The values are X-nodes
    const xmap = sourceToXMap(source);
    const elements = msgstr.split(/({\w+})/);

    return {
        target: elements.map(element => {
            if (element[0] === "{") {
                const key = element.substring(1, element.length - 1);
                if (!xmap.has(key)) {
                    throw new Error(
                        `Did not find key ${key} in expected xmap.\nSource: ${JSON.stringify(
                            source,
                            null,
                            2
                        )}\nMap: ${JSON.stringify({ keys: Array.from(xmap.keys()) }, null, 2)}`
                    );
                    return null;
                }
                return xmap.get(key);
            }
            return { "#text": element };
        }),
    };
}

const parser = new XMLParser(options);
const content = readFileSync(program.opts().xml);
const json = parser.parse(content);
const xliff = json.find((node: any) => "xliff" in node);
const xfile = xliff.xliff.find((node: any) => "file" in node);
const body = xfile.file.find((node: any) => "body" in node);
const units = body.body.filter((node: any) => "trans-unit" in node);

const pofile = readFileSync(program.opts().po);
const pomap = new Map(PO.parse(pofile.toString()).items.map(item => [item.msgid, item.msgstr[0]]));

units.forEach((unit: any) => {
    const source = unit["trans-unit"].find((node: any) => "source" in node);
    const key = sourceToMsgid(source).trim();

    {
        const translatedString = pomap.get(key);
        if (translatedString !== undefined) {
            unit["trans-unit"].push(poToMappedSource(translatedString, source));
            return;
        }
    }

    {
        const translatedString = pomap.get(specialCases.get(key) ?? "---tombstone---");
        if (translatedString !== undefined) {
            unit["trans-unit"].push(poToMappedSource(translatedString, source));
            return;
        }
    }

    return;
});

const builder = new XMLBuilder({ format: true, preserveOrder: true, ignoreAttributes: false });
const output = builder.build(json);
console.log(output);
