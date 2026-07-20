import assert from "node:assert/strict";
import { test } from "node:test";

import { buildPlan } from "../scripts/hexworld/build.mjs";

test("buildPlan emits per-band tippecanoe runs and both tile-join cuts", () => {
    const plan = buildPlan({ outDir: "/tmp/x", localities: 15000 });
    const joined = plan.map((cmd) => cmd.join(" ")).join("\n");
    assert.match(joined, /tippecanoe .*-Z0 -z2 .*hex-r3/);
    assert.match(joined, /tippecanoe .*-Z3 -z6 .*hex-r4/);
    assert.match(joined, /tippecanoe .*-Z7 -z8 .*hex-r5/);
    assert.match(joined, /tippecanoe .*-Z0 -z2 .*-l borders .*borders-r3/);
    assert.match(joined, /tippecanoe .*-Z3 -z6 .*-l borders .*borders-r4/);
    assert.match(joined, /tippecanoe .*-Z7 -z8 .*-l borders .*borders-r5/);
    assert.match(joined, /tippecanoe .*-Z0 -z8 .*-l places/);
    assert.match(
        joined,
        /tile-join .*hexworld-r4\.pmtiles .*hex-r3\.pmtiles .*hex-r4\.pmtiles .*borders-r3\.pmtiles .*borders-r4\.pmtiles .*places\.pmtiles/,
    );
    assert.match(
        joined,
        /tile-join .*hexworld-r5\.pmtiles .*hex-r3\.pmtiles .*hex-r4\.pmtiles .*hex-r5\.pmtiles .*borders-r3\.pmtiles .*borders-r4\.pmtiles .*borders-r5\.pmtiles .*places\.pmtiles/,
    );
});
