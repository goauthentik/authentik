import * as mdi from "@iconify-json/mdi";
import mermaid from "mermaid";

mermaid.registerIconPacks([
    {
        name: mdi.icons.prefix,
        icons: mdi.icons,
    },
]);
