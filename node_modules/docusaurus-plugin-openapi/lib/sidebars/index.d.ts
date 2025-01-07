import type { DeepPartial } from "utility-types";
import type { InfoPageMetadata, MdxPageMetadata, PropSidebar } from "../types";
import { ApiPageMetadata } from "../types";
interface Options {
    contentPath: string;
    sidebarCollapsible: boolean;
    sidebarCollapsed: boolean;
}
type keys = "type" | "title" | "permalink" | "id" | "source" | "sourceDirName";
type InfoItem = Pick<InfoPageMetadata, keys>;
type ApiItem = Pick<ApiPageMetadata, keys> & {
    api: DeepPartial<ApiPageMetadata["api"]>;
};
type MdxItem = Pick<MdxPageMetadata, keys | "frontMatter">;
type Item = InfoItem | ApiItem | MdxItem;
export declare function generateSidebar(items: Item[], options: Options): Promise<PropSidebar>;
export {};
