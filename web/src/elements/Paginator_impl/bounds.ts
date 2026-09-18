import { Pagination } from "@goauthentik/api";

export interface PaginatorPageBounds {
    page: number;
    totalPages: number;
    startIndex: number;
    endIndex: number;
}

export interface PaginatorState {
    itemCount: number;
    itemsPerPage: number;
    page: number;
}

export const clamp = (min: number, num: number, max: number) => Math.min(Math.max(num, min), max);

export function pageBounds(
    totalItems: number,
    itemsPerPage: number,
    currentPage: number
): PaginatorPageBounds {
    const fixedItemsPerPage = Math.max(1, Math.floor(itemsPerPage || 0));
    const fixedTotalItems = Math.max(0, Math.floor(totalItems || 0));
    const totalPages = fixedTotalItems === 0 ? 0 : Math.ceil(fixedTotalItems / fixedItemsPerPage);
    const page = clamp(Math.floor(currentPage) || 1, 1, Math.max(totalPages, 1));
    const startIndex = totalPages === 0 ? 0 : (page - 1) * fixedItemsPerPage + 1;
    const endIndex = totalPages === 0 ? 0 : Math.min(page * fixedItemsPerPage, fixedTotalItems);

    return {
        page,
        totalPages,
        startIndex,
        endIndex,
    };
}

// This is kinda gross. Django doesn't send us the itemsPerPage that we sent in the request, so we
// have no idea from the response what it'll be. That means the last page gets only the
// "itemsPerPage" as an exact count of the leftovers. It seems to not be broken. (If it starts to
// break, we'll have to have the caller pass in the items-per-page as a parameter.)

export function paginationCalc(pagination: Pagination): PaginatorState {
    const { count: itemCount, current, totalPages, startIndex, endIndex } = pagination;

    if (totalPages < 1 || itemCount < 1) {
        return {
            itemCount: 0,
            itemsPerPage: 1,
            page: 1,
        };
    }

    const itemsPerPage =
        current < totalPages
            ? Math.max(1, endIndex - startIndex + 1)
            : Math.max(1, Math.ceil(itemCount / totalPages));

    return { itemCount, itemsPerPage, page: Math.max(1, current) };
}

export function paginatedBounds(pagination: Pagination): PaginatorPageBounds {
    const { itemCount, itemsPerPage, page } = paginationCalc(pagination);
    return pageBounds(itemCount, itemsPerPage, page);
}
