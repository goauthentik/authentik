import { Compression, type DecompressFunc } from "pmtiles";

export const decompressPMTileBuffer: DecompressFunc = async (buf, compression) => {
    if (compression === Compression.None || compression === Compression.Unknown) {
        return buf;
    }
    if (compression === Compression.Gzip) {
        const stream = new Response(buf).body;
        if (!stream) throw new Error("Empty PMTiles buffer");
        const result = stream.pipeThrough(new DecompressionStream("gzip"));
        return new Response(result).arrayBuffer();
    }
    throw new Error(`PMTiles compression method ${compression} not supported`);
};
