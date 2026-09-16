import type { MermaidConfig } from "mermaid";

/**
 * Resolves PatternFly CSS custom properties into concrete hex colors and maps them onto Mermaid's
 * `themeVariables` keyset.
 *
 * @remarks
 *
 *   Colors are parsed through a 1x1 canvas so that any valid CSS color form (named, rgb/rgba, hsl,
 *   or a `var()` chain) collapses to a hex string Mermaid can consume. Fully transparent values
 *   resolve to `"transparent"`. PatternFly 4 handles light/dark theming at the token level, so a
 *   single token set resolves correctly under either theme — no per-theme branching needed.
 */
export class MermaidThemeAdapter {
    canvas = new OffscreenCanvas(1, 1);
    ctx = this.canvas.getContext("2d");

    constructor(protected computedStyle: CSSStyleDeclaration) {}

    /**
     * Resolve a CSS custom property to a hex color string.
     *
     * @param cssProperty The CSS custom property name to read.
     * @param fallback Color used when the property is unset or empty.
     *
     * @returns A hex color code string, or `"transparent"` for fully transparent values.
     */
    public readHexColorVariable = (cssProperty: string, fallback = "#ff0000"): string => {
        if (!this.ctx) {
            throw new Error("Could not create canvas context for color parsing");
        }

        this.ctx.clearRect(0, 0, 1, 1);
        this.ctx.fillStyle = this.computedStyle.getPropertyValue(cssProperty).trim() || fallback;
        this.ctx.fillRect(0, 0, 1, 1);

        const [r, g, b, a] = this.ctx.getImageData(0, 0, 1, 1).data;

        if (a === 0) {
            return "transparent";
        }

        // eslint-disable-next-line no-bitwise
        return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
    };

    /**
     * Read a surface color, substituting an opaque fallback when the token resolves to
     * `transparent`. Node fills must never be see-through.
     */
    protected readSurface = (cssProperty: string, fallback: string): string => {
        const value = this.readHexColorVariable(cssProperty, fallback);

        return value === "transparent" ? fallback : value;
    };

    /**
     * Map PatternFly tokens onto Mermaid's `themeVariables`.
     *
     * @remarks
     *
     *   Requires `theme: "base"` in the Mermaid config — other built-in themes ignore most of these
     *   overrides.
     */
    public toThemeVariables(darkMode?: boolean): MermaidConfig["themeVariables"] {
        const { readHexColorVariable: read, readSurface } = this;

        const surface = readSurface("--pf-global--palette--purple-50", "#ffffff");
        const surfaceAlt = readSurface("--pf-global--palette--blue-50", surface);
        const surfaceDark = readSurface("--pf-global--palette--black-200", surfaceAlt);

        const textBase = read("--pf-global--palette--purple-700");
        const textSecondary = read(
            darkMode ? "--pf-global--palette--gold-100" : "--pf-global--palette--gold-400",
        );
        const border = read(
            darkMode ? "--pf-global--palette--purple-300" : "--pf-global--palette--purple-700",
        );

        const primaryBorder = read("--pf-global--palette--purple-400");
        const primaryAccent = read("--pf-global--palette--purple-100");
        const primaryAccentText = read("--pf-global--palette--purple-700");

        const success = read("--pf-global--success-color--100");
        const danger = read("--pf-global--danger-color--100");
        const warning = read("--pf-global--warning-color--100");
        const info = read("--pf-global--info-color--100");

        return {
            // Base / canvas
            background: surface,
            mainBkg: surface,
            fontFamily: "var(--ak-font-family-sans-serif)",

            // Primary node
            primaryColor: surface,
            primaryBorderColor: primaryBorder,
            primaryTextColor: textBase,

            // Secondary node
            secondaryColor: surfaceAlt,
            secondaryBorderColor: border,
            secondaryTextColor: textBase,

            // Tertiary node
            tertiaryColor: surfaceDark,
            tertiaryBorderColor: border,
            tertiaryTextColor: textBase,

            // Edges / lines / labels
            lineColor: textSecondary,
            edgeLabelBackground: surface,
            titleColor: textBase,

            // Generic node fallbacks
            nodeBorder: border,
            nodeTextColor: textBase,

            // Clusters / subgraphs
            clusterBkg: surfaceDark,
            clusterBorder: border,

            // Notes
            noteBkgColor: warning,
            noteTextColor: textBase,
            noteBorderColor: border,

            // Brand accents (classDef / linkStyle)
            primaryColorAccent: primaryAccent,
            primaryTextColorAccent: primaryAccentText,

            // Status (state / git / quadrant diagrams)
            successColor: success,
            errorColor: danger,
            warningColor: warning,
            infoColor: info,

            // Sequence / state actors
            actorBkg: surface,
            actorBorder: border,
            actorTextColor: textBase,
            labelBoxBkgColor: surface,
            labelTextColor: textBase,
        };
    }

    /**
     * Semantic accent colors for emitting `linkStyle` / `classDef` directives into diagram source
     * (e.g. coloring policy pass/fail edges).
     */
    public toAccents() {
        const { readHexColorVariable: read } = this;

        return {
            success: read("--pf-global--success-color--100"),
            danger: read("--pf-global--danger-color--100"),
            warning: read("--pf-global--warning-color--100"),
            info: read("--pf-global--info-color--100"),
            primary: read("--pf-global--palette--purple-100"),
        };
    }
}
