import { execSync } from "child_process";
import { fileURLToPath } from "url";
import { readFileSync, writeFileSync } from "fs";
import path from "path";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const structureFilePath = path.join(
    __dirname,
    "../docs/customize/blueprints/v1/structure.md",
);

const cmd = ["git", "ls-remote", "--tags", "origin"].join(" ");
const tagblob = execSync(cmd, { encoding: "utf8" });
const itsadate = /\d{4}\.\d{1,2}\.\d{1,2}$/;
const sortfn = (d1, d2) => {
    const [y1, m1, y2, m2] = [d1[0], d1[1], d2[0], d2[1]].map((s) =>
        parseInt(s, 10),
    );
    return y1 < y2 ? 1 : y1 > y2 ? -1 : m1 < m2 ? 1 : m1 > m2 ? -1 : 0;
};

const taglines = tagblob
    .split("\n")
    .filter((line) => itsadate.test(line))
    .map((line) =>
        line
            .split("\t")[1]
            .replace("refs/tags/version/", "")
            .replace(/\.\d{1,2}$/, "")
            .split("."),
    )
    .toSorted(sortfn)
    .map(([a, b]) => `${a}-${b}`)
    .reduce((acc, a) => (acc.includes(a) ? acc : [...acc, a]), []);

const results = await Promise.allSettled(
    taglines.map((version) =>
        fetch(
            `https://version-${version}.goauthentik.io/blueprints/schema.json`,
            {
                method: "HEAD",
            },
        ),
    ),
);

const version = /version-(\d{4}-\d{1,2})/;

const valid = results
    .filter(
        (result) =>
            result.status === "fulfilled" && result.value.status === 200,
    )
    .map((result) => result.value.url)
    .map((url) => {
        const thedate = version.exec(url)[1];
        return `- [Version ${thedate.replace("-", ".")}](${url})`;
    });

const structurefile = readFileSync(structureFilePath, "utf-8");
const schemablock =
    /<Collapse title="Available Older Blueprint Schemas">.*?<\/Collapse>/m;

writeFileSync(
    structureFilePath,
    structurefile.replace(
        schemablock,
        `<Collapse title="Available Older Blueprint Schemas">
${valid.join("\n")}
</Collapse>`,
    ),
);
