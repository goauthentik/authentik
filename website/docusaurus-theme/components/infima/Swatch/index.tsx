import styles from "./styles.module.css";

import {
    useComputedPalette,
    useComputedUtilityColors,
} from "@goauthentik/docusaurus-theme/components/infima/shared.ts";

import { useColorMode } from "@docusaurus/theme-common";
import { useState } from "react";

interface ColorSwatchProps {
    cssVar: string;
    label: string;
    hex: string | null;
    contrastColor: string;
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
    name: string;
}

export const ColorGroup: React.FC<ColorGroupProps> = ({ name }) => {
    const { colorMode } = useColorMode();
    const palette = useComputedPalette(colorMode);
    const group = palette.get(name);

    if (!group) {
        return null;
    }

    return (
        <>
            <div className={styles.colorGrid}>
                {group.map((color) => (
                    <ColorSwatch
                        key={color.cssVar}
                        cssVar={color.cssVar}
                        label={color.label}
                        hex={color.hex}
                        contrastColor={color.contrastColor}
                    />
                ))}
            </div>
        </>
    );
};

export const UtilityColors: React.FC = () => {
    const { colorMode } = useColorMode();
    const utilityColors = useComputedUtilityColors(colorMode);

    return (
        <div className={styles.utilityGrid}>
            {utilityColors.map((color) => (
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

export const InfimaColorPalette: React.FC = () => {
    const { colorMode } = useColorMode();
    const palette = useComputedPalette(colorMode);

    return (
        <>
            <div className="container margin-vert--md">
                <strong>Current Mode: {colorMode === "dark" ? "Dark" : "Light"}</strong>
            </div>
            {/* {palette.map((group) => (
                <ColorGroup key={group.name} group={group} />
            ))} */}
        </>
    );
};
