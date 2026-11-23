import { createPfGlobal, instance } from "../shared.js";

createPfGlobal("BorderRadius")(instance, {
    sm: "@radius.sm",
    lg: "@radius.pill",
});
