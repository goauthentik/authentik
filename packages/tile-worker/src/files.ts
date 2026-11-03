import { TileType } from "pmtiles";

export type TileFileExtension = "avif" | "jpg" | "mvt" | "png" | "webp";

export const TileFileExtensionMap = new Map<TileFileExtension, TileType>([
    ["avif", TileType.Avif],
    ["jpg", TileType.Jpeg],
    ["mvt", TileType.Mvt],
    ["png", TileType.Png],
    ["webp", TileType.Webp],
]);

export const TileTypeFileExtensionMap = new Map<TileType, TileFileExtension>(
    Array.from(TileFileExtensionMap, ([k, v]) => [v, k]),
);

export const TileTypeContentType: Record<TileType, string> = {
    [TileType.Unknown]: "application/octet-stream",
    [TileType.Avif]: "image/avif",
    [TileType.Jpeg]: "image/jpeg",
    [TileType.Mvt]: "application/x-protobuf",
    [TileType.Png]: "image/png",
    [TileType.Webp]: "image/webp",
};
