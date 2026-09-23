const CSS_URL = "./index.css";
const DARK_THEME = "dark";

const clamp = (v) => Math.min(1, Math.max(0, v));

/* Taken from https://github.com/3fn/DesignerPunk/, but there seem to be a lot of them, all
 * converging on the same magic numbers; this particular set is straight-up AI coded.
 */

function oklchToSrgb(L, C, hDeg) {
    const h = (hDeg * Math.PI) / 180;
    const a = C * Math.cos(h);
    const b = C * Math.sin(h);

    const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
    const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
    const s_ = L - 0.0894841775 * a - 1.291485548 * b;

    const l = l_ ** 3;
    const m = m_ ** 3;
    const s = s_ ** 3;

    const lin = [
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
    ];

    return lin.map((c) => clamp(c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055));
}

function parseColor(value) {
    if (!value) return null;
    const v = value.trim();

    const ok = v.match(
        /oklch\(\s*([\d.]+%?)\s+([\d.]+%?)\s+([\d.]+)(?:deg)?(?:\s*\/\s*([\d.]+%?))?/i,
    );
    if (ok) {
        const num = (raw, scale) =>
            raw.endsWith("%") ? (parseFloat(raw) / 100) * scale : parseFloat(raw);
        return oklchToSrgb(num(ok[1], 1), num(ok[2], 0.4), parseFloat(ok[3]));
    }

    const hex = v.match(/^#([0-9a-f]{3,8})$/i);
    if (hex) {
        let h = hex[1];
        if (h.length === 3 || h.length === 4) {
            h = [...h].map((c) => c + c).join("");
        }
        return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
    }

    const rgb = v.match(/rgba?\(([^)]+)\)/i);
    if (rgb) {
        const parts = rgb[1]
            .split(/[\s,/]+/)
            .filter(Boolean)
            .map(parseFloat);
        return parts.slice(0, 3).map((c) => clamp(c / 255));
    }

    return null;
}

function luminance(rgb) {
    const lin = (c) => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
    return 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2]);
}

function contrastRatio(a, b) {
    if (!a || !b) return null;
    const la = luminance(a);
    const lb = luminance(b);
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

function toHex(rgb) {
    if (!rgb) return "";
    return (
        "#" +
        rgb
            .map((c) =>
                Math.round(c * 255)
                    .toString(16)
                    .padStart(2, "0"),
            )
            .join("")
    );
}

// ------------------------------------------------------------------
// Parse dist/index.css.
// ------------------------------------------------------------------

/**
 * Walk a stylesheet with a brace counter, yielding every innermost
 * block along with the selector path that encloses it. Comments are
 * stripped first so the file's banner does not attach itself to the
 * :root selector.
 */
function parseStylesheet(text) {
    const hexes = new Map();
    for (const m of text.matchAll(/(--[\w-]+)\s*:[^;]*?\/\*\s*(#[0-9a-fA-F]{3,8})\s*\*\//g)) {
        hexes.set(m[1], m[2]);
    }

    const stripped = text.replace(/\/\*[\s\S]*?\*\//g, "");

    const blocks = [];
    const stack = [];
    let buf = "";
    for (const ch of stripped) {
        if (ch === "{") {
            stack.push(buf.trim());
            buf = "";
        } else if (ch === "}") {
            const selector = stack.pop() ?? "";
            blocks.push({ path: [...stack, selector], body: buf });
            buf = "";
        } else {
            buf += ch;
        }
    }

    for (const block of blocks) {
        block.decls = [];
        for (const m of block.body.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
            block.decls.push({
                name: m[1],
                authored: m[2].trim(),
                hex: hexes.get(m[1]) ?? null,
            });
        }
    }

    return blocks;
}

const resolve = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

const probe = document.createElement("div");
probe.style.cssText = "position:absolute;visibility:hidden;height:0";
document.body.append(probe);

function toPx(value) {
    probe.style.width = "0";
    probe.style.width = value;
    const px = probe.getBoundingClientRect().width;
    return Number.isFinite(px) && px > 0 ? px : 0;
}

const el = (tag, props = {}, ...children) => {
    const node = Object.assign(document.createElement(tag), props);
    for (const child of children.flat()) {
        if (child == null || child === false) continue;
        node.append(child);
    }
    return node;
};

const name = (token) => el("span", { className: "token-name", textContent: token });
const value = (text) => el("span", { className: "token-value", textContent: text });
const badge = (text, variant) =>
    el("span", {
        className: variant ? `badge badge--${variant}` : "badge",
        textContent: text,
    });

const rung = (token, prefix) => token.slice(prefix.length);

// The background colors, text and item colors colors, and the WCAG threshold for readability.
const COLOR_GROUPS = [
    {
        title: "Brand",
        tokens: [
            "--ak-global--color--accent",
            "--ak-global--color--primary",
            "--ak-global--color--primary--hover",
        ],
        against: "--ak-global--color--surface",
        threshold: 3,
    },
    {
        title: "Text",
        tokens: ["--ak-global--color--text", "--ak-global--color--text--muted"],
        against: "--ak-global--color--surface",
        threshold: 4.5,
    },
    {
        title: "Link",
        tokens: [
            "--ak-global--color--link",
            "--ak-global--color--link--hover",
            "--ak-global--color--link--visited",
        ],
        against: "--ak-global--color--surface",
        threshold: 4.5,
    },
    {
        title: "Surface",
        tokens: [
            "--ak-global--color--surface",
            "--ak-global--color--surface--raised",
            "--ak-global--color--surface--muted",
        ],
        against: "--ak-global--color--text",
        threshold: 4.5,
        ringed: true,
    },
    {
        title: "Border",
        tokens: ["--ak-global--color--border", "--ak-global--color--border--strong"],
        against: "--ak-global--color--surface",
        threshold: 3,
    },
    {
        title: "Status",
        tokens: [
            "--ak-global--color--info",
            "--ak-global--color--success",
            "--ak-global--color--warning",
            "--ak-global--color--danger",
        ],
        against: "--ak-global--color--surface",
        threshold: 3,
    },
];

// Patternfly icons, since these aren't encoded in either Fonts or Theme.

const PF_ICONS = [
    ["user", 0xe91e],
    ["users", 0xe91f],
    ["key", 0xe924],
    ["locked", 0xe923],
    ["unlocked", 0xe922],
    ["security", 0xe946],
    ["private", 0xe914],
    ["enterprise", 0xe906],
    ["server", 0xe90d],
    ["cluster", 0xe620],
    ["network", 0xe909],
    ["domain", 0xe919],
    ["applications", 0xe936],
    ["catalog", 0xe953],
    ["blueprint", 0xe915],
    ["automation", 0xe937],
    ["integration", 0xe948],
    ["migration", 0xe931],
    ["bell", 0xe952],
    ["ok", 0xe602],
    ["error-circle-o", 0xe926],
    ["warning-triangle", 0xe975],
    ["info", 0xe92b],
    ["help", 0xe605],
    ["history", 0xe617],
    ["edit", 0xe60a],
    ["filter", 0xe943],
    ["export", 0xe616],
    ["import", 0xe615],
    ["plugged", 0xe96a],
    ["connected", 0xe938],
    ["disconnected", 0xe955],
    ["pending", 0xe964],
    ["in-progress", 0xe933],
    ["topology", 0xe608],
    ["module", 0xe959],
    ["tenant", 0xe916],
    ["task", 0xe974],
    ["project", 0xe96c],
    ["repository", 0xe90b],
    ["globe-route", 0xe958],
    ["monitoring", 0xe95a],
];

const FA_ICONS = [
    ["sign-in-alt", 0xf2f6],
    ["sign-out-alt", 0xf2f5],
    ["fingerprint", 0xf577],
    ["id-card", 0xf2c2],
    ["id-badge", 0xf2c1],
    ["shield-alt", 0xf3ed],
    ["user-shield", 0xf505],
    ["user-lock", 0xf502],
    ["lock", 0xf023],
    ["lock-open", 0xf3c1],
    ["unlock", 0xf09c],
    ["key", 0xf084],
    ["envelope", 0xf0e0],
    ["mobile-alt", 0xf3cd],
    ["qrcode", 0xf029],
    ["check-circle", 0xf058],
    ["times-circle", 0xf057],
    ["exclamation-circle", 0xf06a],
    ["exclamation-triangle", 0xf071],
    ["question-circle", 0xf059],
    ["info-circle", 0xf05a],
    ["cog", 0xf013],
    ["cogs", 0xf085],
    ["search", 0xf002],
    ["plus", 0xf067],
    ["trash", 0xf1f8],
    ["pencil-alt", 0xf303],
    ["link", 0xf0c1],
    ["external-link-alt", 0xf35d],
    ["clock", 0xf017],
    ["calendar-alt", 0xf073],
    ["code", 0xf121],
    ["terminal", 0xf120],
    ["database", 0xf1c0],
    ["cloud", 0xf0c2],
    ["globe", 0xf0ac],
    ["download", 0xf019],
    ["upload", 0xf093],
    ["sync", 0xf021],
    ["redo", 0xf01e],
    ["eye", 0xf06e],
    ["eye-slash", 0xf070],
    ["bars", 0xf0c9],
    ["ellipsis-v", 0xf142],
    ["chevron-right", 0xf054],
    ["chevron-down", 0xf078],
    ["arrow-right", 0xf061],
    ["copy", 0xf0c5],
    ["file-alt", 0xf15c],
    ["clipboard-check", 0xf46c],
];

const PANGRAM = "Sphinx of black quartz, judge my vow";
const PROSE =
    "authentik is an IdP (Identity Provider) and SSO (Single Sign-On) platform that is built with security at the forefront of every piece of code and every feature, with an emphasis on flexibility and versatility.";

const blocks = parseStylesheet(await fetch(CSS_URL).then((r) => r.text()));

// The unconditional :root block — the canonical token list, in order. */
const rootBlock = blocks.find((b) => b.path.length === 1 && b.path[0].includes(":root"));
if (!rootBlock) throw new Error(`no top-level :root block in ${CSS_URL}`);

const TOKENS = rootBlock.decls;

// Styleframe emits a theme as a list of selectors, and we've got several. Check them all.
const isThemeSelector = (selector, theme) => {
    const branches = new Set([`.${theme}-theme`, `[data-theme="${theme}"]`]);
    return selector.split(",").some((branch) => branches.has(branch.trim()));
};

const darkNames = new Set(
    blocks
        .filter((b) => isThemeSelector(b.path.at(-1) ?? "", DARK_THEME))
        .flatMap((b) => b.decls.map((d) => d.name)),
);

if (!darkNames.size) {
    console.warn(
        `[demo] no ${DARK_THEME}-theme block in ${CSS_URL}; every token will read as un-themed`,
    );
}

const mediaNames = new Set(
    blocks
        .filter((b) => b.path.some((p) => p.startsWith("@media")))
        .flatMap((b) => b.decls.map((d) => d.name)),
);

const byPrefix = (prefix) => TOKENS.filter((t) => t.name.startsWith(prefix));

/** Tokens the page has actually rendered, for the audit at the end. */
const rendered = new Set();
const mark = (token) => {
    rendered.add(token.name ?? token);
    return token;
};

// ------------------------------------------------------------------
// Color.
// ------------------------------------------------------------------

function contrastBadge(swatchToken, counterpartToken, threshold) {
    const ratio = contrastRatio(
        parseColor(resolve(swatchToken)),
        parseColor(resolve(counterpartToken)),
    );
    if (ratio == null) return null;
    const variant = ratio >= 4.5 ? "pass" : ratio >= threshold ? "mid" : "fail";
    const other = rung(counterpartToken, "--ak-global--color--");
    return badge(`${ratio.toFixed(2)}:1 vs ${other}`, variant);
}

function renderColors() {
    const host = document.getElementById("color-groups");
    host.replaceChildren();

    const claimed = new Set(COLOR_GROUPS.flatMap((g) => g.tokens));
    const groups = [...COLOR_GROUPS];
    const orphans = byPrefix("--ak-global--color--")
        .filter((t) => !claimed.has(t.name))
        .map((t) => t.name);
    if (orphans.length) {
        groups.push({
            title: "Ungrouped",
            tokens: orphans,
            against: "--ak-global--color--surface",
            threshold: 3,
        });
    }

    for (const group of groups) {
        const cells = group.tokens
            .map((tokenName) => {
                const token = TOKENS.find((t) => t.name === tokenName);
                if (!token) return null;
                mark(token);

                const effective = resolve(tokenName);
                const rgb = parseColor(effective);
                const overridden = darkNames.has(tokenName);
                // The :root definition may be a var() alias, but a
                // theme block can replace it with a literal — so
                // the alias only holds while that block is inactive.
                const inDark = document.documentElement.dataset.theme === "dark";
                const isAlias = token.authored.startsWith("var(") && !(inDark && overridden);

                return el(
                    "div",
                    { className: "swatch" },
                    el("div", {
                        className: "swatch__chip" + (group.ringed ? " swatch__chip--ringed" : ""),
                        style: `background:${effective}`,
                    }),
                    el(
                        "div",
                        { className: "swatch__body" },
                        name(tokenName),
                        value(effective),
                        el(
                            "div",
                            { className: "badges" },
                            token.hex ? badge(token.hex) : badge(toHex(rgb)),
                            isAlias
                                ? badge(
                                      `alias of ${token.authored
                                          .match(/var\(\s*(--[\w-]+)/)[1]
                                          .replace("--ak-global--color--", "")}`,
                                  )
                                : null,
                            // Contrast is symmetric, so the swatch
                            // and its counterpart are just the pair.
                            contrastBadge(tokenName, group.against, group.threshold),
                            !overridden && !isAlias
                                ? badge("no dark override", "fallthrough")
                                : null,
                        ),
                    ),
                );
            })
            .filter(Boolean);

        host.append(
            el("h3", { className: "subhead", textContent: group.title }),
            el("div", { className: "grid" }, cells),
        );
    }

    document.getElementById("color-count").textContent =
        `${byPrefix("--ak-global--color--").length} tokens`;
}

// ------------------------------------------------------------------
// Typography.
// ------------------------------------------------------------------

function renderTypography() {
    const families = byPrefix("--ak-global--font-family--");
    const sizes = byPrefix("--ak-global--font-size--");
    const weights = byPrefix("--ak-global--font-weight--");
    const leadings = byPrefix("--ak-global--line-height--");

    document.getElementById("families").replaceChildren(
        ...families.map((token) => {
            mark(token);
            const effective = resolve(token.name);
            return el(
                "div",
                { className: "specimen" },
                el("div", {
                    className: "specimen__display",
                    style: `font-family:${effective}`,
                    textContent: "Aa",
                }),
                name(token.name),
                el("br"),
                value(token.authored.startsWith("var(") ? token.authored : effective),
                el("p", {
                    className: "specimen__para",
                    style: `font-family:${effective}`,
                    textContent: PANGRAM,
                }),
            );
        }),
    );

    document.getElementById("sizes").replaceChildren(
        ...sizes.map((token) => {
            mark(token);
            const effective = resolve(token.name);
            return el(
                "div",
                { className: "ramp__row" },
                name(token.name),
                value(`${effective} · ${toPx(effective).toFixed(1)}px`),
                el("div", {
                    className: "ramp__sample",
                    style: `font-size:${effective}`,
                    textContent: PANGRAM,
                }),
            );
        }),
    );

    const FACES = [
        ["--ak-global--font-family--display", "RedHatDisplay", "300–900"],
        ["--ak-global--font-family--sans-serif", "RedHatText", "400–500"],
        ["--ak-global--font-family--monospace", "RedHatMono", "300–700"],
    ];
    document.getElementById("weights").replaceChildren(
        ...FACES.map(([familyToken, face, range]) =>
            el(
                "div",
                { className: "weights__col" },
                el("h4", { textContent: `${face} — declared ${range}` }),
                ...weights.map((token) => {
                    mark(token);
                    const w = resolve(token.name);
                    return el(
                        "div",
                        { className: "weights__row" },
                        el("span", {
                            style: `font-family:${resolve(familyToken)};font-weight:${w}`,
                            textContent: "Identity",
                        }),
                        value(`${rung(token.name, "--ak-global--font-weight--")} ${w}`),
                    );
                }),
            ),
        ),
    );

    document.getElementById("leading").replaceChildren(
        ...leadings.map((token) => {
            mark(token);
            const effective = resolve(token.name);
            return el(
                "div",
                { className: "specimen" },
                name(token.name),
                ": ",
                value(effective),
                el("p", {
                    className: "specimen__para",
                    style: `line-height:${effective}`,
                    textContent: PROSE,
                }),
            );
        }),
    );

    document.getElementById("type-count").textContent =
        `${families.length + sizes.length + weights.length + leadings.length} tokens`;
}

// ------------------------------------------------------------------
// Spacing, shape.
// ------------------------------------------------------------------

function renderSpacing() {
    const spaces = byPrefix("--ak-global--space--");
    document.getElementById("spaces").replaceChildren(
        ...spaces.flatMap((token) => {
            mark(token);
            const effective = resolve(token.name);
            return [
                name(token.name),
                value(`${effective} · ${toPx(effective).toFixed(0)}px`),
                el("div", { className: "bar", style: `width:${effective}` }),
            ];
        }),
    );
    document.getElementById("space-count").textContent = `${spaces.length} tokens`;
}

function renderShape() {
    const radii = byPrefix("--ak-global--radius--");
    const strokes = byPrefix("--ak-global--border-width--");

    document.getElementById("radii").replaceChildren(
        ...radii.map((token) => {
            mark(token);
            const effective = resolve(token.name);
            return el(
                "div",
                { className: "shape-chip" },
                el("div", {
                    className: "shape-chip__box",
                    style: `border-radius:${effective}`,
                }),
                name(token.name),
                value(effective),
            );
        }),
    );

    document.getElementById("strokes").replaceChildren(
        ...strokes.map((token) => {
            mark(token);
            const effective = resolve(token.name);
            return el(
                "div",
                { className: "shape-chip" },
                el("div", {
                    className: "stroke-chip__box",
                    style: `border-width:${effective}`,
                }),
                name(token.name),
                value(effective),
            );
        }),
    );

    document.getElementById("shape-count").textContent = `${radii.length + strokes.length} tokens`;
}

// ------------------------------------------------------------------
// Surfaces, shadows.
// ------------------------------------------------------------------

function renderSurfaces() {
    const planes = byPrefix("--ak-global--color--surface");
    const shadows = byPrefix("--ak-global--box-shadow--");

    document.getElementById("surface-planes").replaceChildren(
        ...planes.map((token) => {
            const effective = resolve(token.name);
            return el(
                "div",
                {
                    className: "surface-demo",
                    style: `background:${effective}`,
                },
                name(token.name),
                el("br"),
                value(effective),
            );
        }),
    );

    document.getElementById("shadows").replaceChildren(
        ...shadows.map((token) => {
            mark(token);
            const effective = resolve(token.name);
            return el(
                "div",
                { className: "shadow-card", style: `box-shadow:${effective}` },
                name(token.name),
                badge(
                    darkNames.has(token.name) ? "themed" : "no dark override",
                    darkNames.has(token.name) ? null : "fallthrough",
                ),
            );
        }),
    );

    document.getElementById("surface-count").textContent =
        `${planes.length} planes · ${shadows.length} shadows`;
}

// ------------------------------------------------------------------
// Motion.
// ------------------------------------------------------------------

function renderMotion() {
    const motion = [...byPrefix("--ak-global--duration--"), ...byPrefix("--ak-global--easing--")];
    document.getElementById("motion-tokens").replaceChildren(
        ...motion.map((token) => {
            mark(token);
            return el(
                "div",
                { className: "specimen" },
                name(token.name),
                el("br"),
                value(resolve(token.name)),
                el(
                    "div",
                    { className: "badges" },
                    mediaNames.has(token.name) ? badge("zeroed by prefers-reduced-motion") : null,
                ),
            );
        }),
    );

    const prefersReduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.getElementById("motion-state").textContent =
        ` — --ak-global--duration--normal resolves to ${resolve("--ak-global--duration--normal")}; ` +
        `prefers-reduced-motion is ${prefersReduced ? "on" : "off"}; ` +
        `data-theme is "${document.documentElement.dataset.theme || "(unset)"}". ` +
        `Note that data-theme holds one value, so "dark" and "reduced" cannot both apply.`;

    document.getElementById("motion-count").textContent = `${motion.length} tokens`;
}

// ------------------------------------------------------------------
// Layering.
// ------------------------------------------------------------------

function renderLayering() {
    const zs = byPrefix("--ak-global--z-index--");
    document.getElementById("zstack").replaceChildren(
        ...zs.map((token, i) => {
            mark(token);
            const effective = resolve(token.name);
            return el(
                "div",
                {
                    className: "zstack__layer",
                    style: `left:${i * 4.5}rem;z-index:${effective}`,
                },
                name(token.name),
                value(effective),
            );
        }),
    );
    document.getElementById("z-count").textContent = `${zs.length} tokens`;
}

// ------------------------------------------------------------------
// Icons.
// ------------------------------------------------------------------

function renderIcons() {
    const cells = (set, variant, prefix) =>
        set.map(([iconName, cp]) =>
            el(
                "div",
                { className: "icon-cell" },
                el("i", {
                    className: `glyph glyph--${variant}`,
                    textContent: String.fromCodePoint(cp),
                    ariaHidden: "true",
                }),
                el("span", {
                    className: "icon-cell__name",
                    textContent: `${prefix}${iconName}`,
                }),
                value(`\\${cp.toString(16)}`),
            ),
        );

    document.getElementById("icons-pf").replaceChildren(...cells(PF_ICONS, "pf", "pf-icon-"));
    document.getElementById("icons-fa").replaceChildren(...cells(FA_ICONS, "fa", "fa-"));
    document.getElementById("icon-count").textContent =
        `${PF_ICONS.length} pficon · ${FA_ICONS.length} fa-solid, of the full sets`;
}

// ------------------------------------------------------------------
// Overview and audit.
// ------------------------------------------------------------------

function renderOverview() {
    const categories = new Set(
        TOKENS.map((t) => t.name.replace(/^--ak-global--/, "").split("--")[0]),
    );
    console.log("C:", categories);
    document.getElementById("stats").replaceChildren(
        ...[
            [TOKENS.length, "tokens in :root"],
            [categories.size, "categories"],
            [darkNames.size, "dark overrides"],
            [byPrefix("--ak-global--color--").length, "color tokens"],
            [TOKENS.filter((t) => t.authored.startsWith("var(")).length, "aliases"],
        ].map(([v, label]) =>
            el(
                "div",
                { className: "stat" },
                el("div", { className: "stat__value", textContent: String(v) }),
                el("div", { className: "stat__label", textContent: label }),
            ),
        ),
    );

    document.getElementById("tokens-count").textContent = `${TOKENS.length} in :root`;
    document.getElementById("meta-line").textContent =
        `${TOKENS.length} tokens · ${darkNames.size} dark overrides · design system reference`;
}

function renderAudit() {
    const host = document.getElementById("audit");
    const missing = TOKENS.filter((t) => !rendered.has(t.name)).map((t) => t.name);
    const unknownDark = [...darkNames].filter((n) => !TOKENS.some((t) => t.name === n));

    host.replaceChildren();
    if (!missing.length && !unknownDark.length) {
        host.dataset.state = "ok";
        host.append(
            el("strong", {
                textContent: `Complete: all ${TOKENS.length} tokens in dist/index.css are represented above.`,
            }),
        );
        return;
    }

    host.dataset.state = missing.length ? "stale" : "error";
    host.append(el("strong", { textContent: "This page is out of date with the build." }));
    if (missing.length) {
        host.append(
            el(
                "div",
                {},
                `${missing.length} token(s) exist in dist/index.css but no section renders them:`,
                el("ul", {}, ...missing.map((n) => el("li", {}, el("code", { textContent: n })))),
            ),
        );
    }
    if (unknownDark.length) {
        host.append(
            el(
                "div",
                {},
                `${unknownDark.length} token(s) are defined only in the ${DARK_THEME} theme, with no :root default:`,
                el(
                    "ul",
                    {},
                    ...unknownDark.map((n) => el("li", {}, el("code", { textContent: n }))),
                ),
            ),
        );
    }
}

function renderThemed() {
    rendered.clear();
    renderOverview();
    renderColors();
    renderTypography();
    renderSpacing();
    renderShape();
    renderSurfaces();
    renderMotion();
    renderLayering();
    renderAudit();
}

for (const button of document.querySelectorAll("[data-theme-value]")) {
    button.addEventListener("click", () => {
        document.documentElement.dataset.theme = button.dataset.themeValue;
        for (const other of document.querySelectorAll("[data-theme-value]")) {
            other.setAttribute("aria-pressed", String(other === button));
        }
        renderThemed();
    });
}

const track = document.getElementById("motion-track");
document.getElementById("motion-run").addEventListener("click", () => {
    track.dataset.run = track.dataset.run === "true" ? "false" : "true";
});

renderIcons();
renderThemed();

document.fonts?.ready.then(renderThemed);
