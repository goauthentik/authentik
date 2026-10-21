import { buildPlan } from "../scripts/build-hexworld.ts";

import { expect, test } from "vitest";

test("buildPlan emits per-band tippecanoe runs and both tile-join cuts", () => {
    const plan = buildPlan({ outDir: "/tmp/x", localities: 15000 });
    const joined = plan.map((cmd) => cmd.join(" ")).join("\n");
    expect(joined).toMatch(/tippecanoe .*-Z0 -z2 .*hex-r3/);
    // Cross-fade overlap: res-3 geometry rides one tile zoom into the res-4
    // band so the style can fade between grids instead of swapping them.
    expect(joined).toMatch(/tippecanoe .*-Z3 -z3 .*hex-r3-fade/);
    expect(joined).toMatch(/tippecanoe .*-Z3 -z3 .*-l borders .*borders-r3-fade/);
    expect(joined).toMatch(/tippecanoe .*-Z3 -z6 .*hex-r4/);
    expect(joined).toMatch(/tippecanoe .*-Z7 -z7 .*hex-r5/);
    expect(joined).toMatch(/tippecanoe .*-Z0 -z2 .*-l borders .*borders-r3/);
    expect(joined).toMatch(/tippecanoe .*-Z3 -z6 .*-l borders .*borders-r4/);
    expect(joined).toMatch(/tippecanoe .*-Z7 -z7 .*-l borders .*borders-r5/);
    expect(joined).toMatch(/tippecanoe .*-Z0 -z7 .*-l places/);
    expect(joined).toMatch(
        /tile-join .*hexworld-plain\.pmtiles .*hex-r3\.pmtiles .*hex-r3-fade\.pmtiles .*hex-r4\.pmtiles .*borders-r3\.pmtiles .*borders-r3-fade\.pmtiles .*borders-r4\.pmtiles .*places\.pmtiles/,
    );
    expect(joined).toMatch(
        /tile-join .*hexworld-detail\.pmtiles .*hex-r3\.pmtiles .*hex-r4\.pmtiles .*hex-r4-base\.pmtiles .*hex-r5\.pmtiles .*borders-r3\.pmtiles .*borders-r4\.pmtiles .*borders-r4-base\.pmtiles .*borders-r5\.pmtiles .*places\.pmtiles/,
    );
});
