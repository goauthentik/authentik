import styles from "./styles.module.css";

import {
    ColorEntry,
    ColorGroupProp,
    computeColor,
    ComputedColor,
    createComputedColorGroup,
    Prefix,
} from "@goauthentik/docusaurus-theme/components/infima/shared.ts";

import { useColorMode } from "@docusaurus/theme-common";
import { useMemo, useState } from "react";

interface ColorSwatchProps extends ComputedColor {
    showVar?: boolean;
}

const ColorSwatch: React.FC<ColorSwatchProps> = ({
    cssVar,
    label,
    hex,
    contrastColor,
    showVar = true,
}) => {
    const [copied, setCopied] = useState(false);

    const copyToClipboard = async (): Promise<void> => {
        try {
            await navigator.clipboard.writeText(cssVar);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    };

    return (
        <div
            onClick={copyToClipboard}
            className={styles.swatch}
            style={{
                backgroundColor: `var(${cssVar})`,
                color: contrastColor,
            }}
        >
            <div className={styles.swatchLabel}>{label}</div>
            {showVar ? <div className={styles.swatchVar}>{cssVar}</div> : null}
            <div className={styles.swatchHex}>{hex || "—"}</div>
            {copied ? <div className={styles.copiedToast}>Copied!</div> : null}
        </div>
    );
};

export interface ColorGroupProps {
    group?: ColorGroupProp;
}

export const ColorGroup: React.FC<ColorGroupProps> = ({ group }) => {
    const { colorMode } = useColorMode();

    if (!group) {
        throw new TypeError("Invalid color group name");
    }

    const computed = useMemo(() => createComputedColorGroup(group, colorMode), [group, colorMode]);

    return (
        <div className={styles.colorGrid}>
            {computed.colors.map((color) => (
                <ColorSwatch
                    key={color.cssVar}
                    cssVar={color.cssVar}
                    label={color.label}
                    hex={color.hex}
                    contrastColor={color.contrastColor}
                />
            ))}
        </div>
    );
};

export interface PaletteGroupProps {
    entries?: Iterable<ColorEntry>;
}

export const PaletteGroup: React.FC<PaletteGroupProps> = ({ entries }) => {
    const { colorMode } = useColorMode();

    if (!entries) {
        throw new TypeError("Invalid utility color entries");
    }

    const swatchProps: ColorSwatchProps[] = useMemo(() => {
        return Array.from(entries, ([label, partialCSSVar]) => {
            const cssVar = `${Prefix.Infima}${partialCSSVar}`;
            const { hex, contrastColor } = computeColor(cssVar);

            return { cssVar, label, hex, contrastColor, showVar: true, colorMode };
        });
    }, [entries, colorMode]);

    return (
        <div className={styles.colorGrid}>
            {swatchProps.map((props) => (
                <ColorSwatch key={props.cssVar} {...props} />
            ))}
        </div>
    );
};
