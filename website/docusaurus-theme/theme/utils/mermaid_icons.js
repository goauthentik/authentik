import * as fa7Regular from "@iconify-json/fa7-regular";
import * as fa7Solid from "@iconify-json/fa7-solid";
import * as mdi from "@iconify-json/mdi";
import mermaid from "mermaid";

mermaid.registerIconPacks([
    {
        name: fa7Regular.icons.prefix,
        icons: fa7Regular.icons,
    },
    {
        name: fa7Solid.icons.prefix,
        icons: fa7Solid.icons,
    },
    {
        name: mdi.icons.prefix,
        icons: mdi.icons,
    },
]);
