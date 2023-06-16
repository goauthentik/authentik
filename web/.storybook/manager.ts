// .storybook/manager.js
import { addons } from "@storybook/manager-api";

import authentikTheme from "./authentikTheme";

addons.setConfig({
    theme: authentikTheme,
});
