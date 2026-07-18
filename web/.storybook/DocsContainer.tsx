import { extendStorybookTheme } from "./theme.js";

import { createUIThemeEffect, resolveUITheme } from "@goauthentik/web/common/theme.ts";

import { DocsContainer, DocsContainerProps } from "@storybook/addon-docs/blocks";
import { useEffect, useMemo, useState } from "react";

export const ThemedDocsContainer: React.FC<DocsContainerProps> = ({
    theme: initialTheme = resolveUITheme(),
    ...props
}) => {
    const [theme, setTheme] = useState(initialTheme);
    const resolvedTheme = useMemo(() => extendStorybookTheme(theme), [theme]);

    useEffect(() => createUIThemeEffect(setTheme), []);

    return <DocsContainer {...props} theme={resolvedTheme} />;
};
