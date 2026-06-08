import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import Ajv from "ajv";
import prettier from "prettier";
import yaml from "yaml";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const integrationsDir = path.resolve(__dirname, "..");
const schemaPath = path.join(integrationsDir, "integration-guide.schema.json");

const schema = JSON.parse(await readFile(schemaPath, "utf8"));
const ajv = new Ajv({ allErrors: true, validateFormats: false, validateSchema: false });
const validate = ajv.compile(schema);

const guidePaths = process.argv.slice(2);

if (guidePaths.length === 0) {
    guidePaths.push("platforms/anthropic/guide.yml");
}

const frontMatterKeys = ["title", "sidebar_label", "support_level", "integration_beta"];

function frontMatterValue(value) {
    return typeof value === "string" && /[:#\n]/.test(value) ? JSON.stringify(value) : value;
}

function indent(text, spaces) {
    const prefix = " ".repeat(spaces);
    return text
        .split("\n")
        .map((line) => (line ? `${prefix}${line}` : line))
        .join("\n");
}

function formatCode(block) {
    const flags = [];
    if (block.show_line_numbers) {
        flags.push("showLineNumbers");
    }
    if (block.title) {
        flags.push(`title=${JSON.stringify(block.title)}`);
    }
    const info = [block.language, ...flags].filter(Boolean).join(" ");
    return `\`\`\`${info}\n${block.text.trimEnd()}\n\`\`\``;
}

function formatListItem(item, marker, depth) {
    const lines = [`${" ".repeat(depth)}${marker} ${item.text}`];
    if (item.blocks?.length) {
        lines.push("");
        lines.push(indent(renderBlocks(item.blocks), depth + 4));
    }
    return lines.join("\n");
}

function renderBlock(block) {
    switch (block.type) {
        case "admonition": {
            const title = block.title ? ` ${block.title}` : "";
            return `:::${block.kind}${title}\n${renderBlocks(block.blocks)}\n:::`;
        }
        case "code":
            return formatCode(block);
        case "component":
            return `<${block.name} />`;
        case "heading":
            return `${"#".repeat(block.level)} ${block.text}`;
        case "list": {
            return block.items
                .map((item, index) =>
                    formatListItem(item, block.style === "ordered" ? `${index + 1}.` : "-", 0),
                )
                .join("\n");
        }
        case "markdown":
            return block.text.trim();
        case "paragraph":
            return block.text;
        case "section":
            return [`${"#".repeat(block.level)} ${block.heading}`, renderBlocks(block.blocks)].join(
                "\n\n",
            );
        case "settings":
            return block.items
                .map((item) => {
                    const lines = [
                        item.value ? `- **${item.label}**: ${item.value}` : `- **${item.label}**:`,
                    ];
                    if (item.blocks?.length) {
                        lines.push(indent(renderBlocks(item.blocks), 4));
                    }
                    return lines.join("\n");
                })
                .join("\n");
        case "table": {
            const header = `| ${block.columns.join(" | ")} |`;
            const divider = `| ${block.columns.map(() => "---").join(" | ")} |`;
            const rows = block.rows.map((row) => `| ${row.join(" | ")} |`);
            return [header, divider, ...rows].join("\n");
        }
        case "tabs": {
            const values = block.items
                .map(
                    (item) =>
                        `    { label: ${JSON.stringify(item.label)}, value: ${JSON.stringify(item.value)} }`,
                )
                .join(",\n");
            const tabs = [
                "<Tabs",
                `  defaultValue=${JSON.stringify(block.default_value)}`,
                "  values={[",
                values,
                "  ]}>",
            ];
            for (const item of block.items) {
                tabs.push(`  <TabItem value=${JSON.stringify(item.value)}>`);
                tabs.push("");
                tabs.push(renderBlocks(item.blocks));
                tabs.push("");
                tabs.push("  </TabItem>");
            }
            tabs.push("</Tabs>");
            return tabs.join("\n");
        }
        default:
            throw new TypeError(`Unsupported block type: ${block.type}`);
    }
}

function renderBlocks(blocks) {
    return blocks.map(renderBlock).join("\n\n");
}

function renderGuide(guide) {
    const frontMatter = frontMatterKeys
        .map((key) => `${key}: ${frontMatterValue(guide.metadata[key])}`)
        .join("\n");
    const imports = guide.imports
        .map((item) => {
            const imported = item.default === false ? `{ ${item.name} }` : item.name;
            return `import ${imported} from ${JSON.stringify(item.from)};`;
        })
        .join("\n");
    const preparationBlocks = [
        {
            type: "paragraph",
            text: "The following placeholders are used in this guide:",
        },
        {
            type: "list",
            style: "unordered",
            items: guide.preparation.placeholders.map((placeholder) => ({
                text: `\`${placeholder.token}\` is ${placeholder.description}`,
            })),
        },
        ...guide.preparation.admonitions,
    ];

    return [
        "---",
        frontMatter,
        "---",
        "",
        "<!-- Generated from guide.yml by scripts/generate-yaml-guides.mjs. -->",
        "",
        imports,
        "",
        `## ${guide.overview.heading}`,
        "",
        `> ${guide.overview.quote.text}`,
        ">",
        `> -- ${guide.overview.quote.source}`,
        "",
        guide.overview.paragraphs.join("\n\n"),
        "",
        "## Preparation",
        "",
        renderBlocks(preparationBlocks),
        "",
        renderBlocks(guide.sections),
        "",
        "## Resources",
        "",
        guide.resources.map((resource) => `- [${resource.title}](${resource.url})`).join("\n"),
        "",
    ]
        .filter((part) => part !== undefined)
        .join("\n")
        .replace(/\n{3,}/g, "\n\n");
}

for (const relativeGuidePath of guidePaths) {
    const guidePath = path.resolve(integrationsDir, relativeGuidePath);
    const source = await readFile(guidePath, "utf8");
    const guide = yaml.parse(source);

    if (!validate(guide)) {
        const errors = validate.errors
            .map((error) => `${error.instancePath || "/"} ${error.message}`)
            .join("\n");
        throw new Error(
            `${relativeGuidePath} does not match integration-guide.schema.json:\n${errors}`,
        );
    }

    const outputPath = path.join(path.dirname(guidePath), "index.mdx");
    const prettierOptions = await prettier.resolveConfig(outputPath);
    const output = await prettier.format(renderGuide(guide), {
        ...prettierOptions,
        filepath: outputPath,
        parser: "mdx",
    });
    await writeFile(outputPath, output, "utf8");
    console.log(`Generated ${path.relative(integrationsDir, outputPath)}`);
}
