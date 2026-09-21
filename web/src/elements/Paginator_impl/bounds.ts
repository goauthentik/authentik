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
    currentPage: number,
): PaginatorPageBounds {
    const fixedItemsPerPage = Math.max(1, Math.floor(itemsPerPage || 0));
    const fixedTotalItems = Math.max(0, Math.floor(totalItems || 0));
    const totalPages = fixedTotalItems === 0 ? 0 : Math.ceil(fixedTotalItems / fixedItemsPerPage);
    const page = clamp(Math.floor(currentPage) || 1, 1, Math.max(totalPages, 1));
    const startIndex = totalPages === 0 ? 0 : (page - 1) * fixedItemsPerPage + 1;
    const endIndex = totalPages === 0 ? 0 : Math.min(page * fixedItemsPerPage, fixedTotalItems);

    console.log("P5:", startIndex, endIndex);

    return {
        page,
        totalPages,
        startIndex,
        endIndex,
    };
}

const defaultPagination = { count: 0, current: 1, totalPages: 1, startIndex: 0, endIndex: 0 };

// This is kinda gross. Django doesn't send us the itemsPerPage that we sent in the request, so we
// can't automatically know from the response what was requested. start_index is always `(page - 1)
// * per_page + 1`, so we recover `per-page` from that. We can't use the client-side perPage feature
// without it being exposed, and lots of current client-side implementations don't expose it, they
// hide it in closures.

export function toPaginator(pagination?: Pagination): PaginatorState {
    const {
        count: itemCount,
        current,
        totalPages,
        startIndex,
        endIndex,
    } = pagination ?? defaultPagination;

    if (totalPages < 1 || itemCount < 1) {
        return {
            itemCount: 0,
            itemsPerPage: 1,
            page: 1,
        };
    }

    const itemsPerPage =
        current > 1
            ? Math.max(1, Math.round((startIndex - 1) / (current - 1)))
            : Math.max(1, endIndex - startIndex + 1);

    return { itemCount, itemsPerPage, page: Math.max(1, current) };
}

export function paginatedBounds(pagination: Pagination): PaginatorPageBounds {
    const { itemCount, itemsPerPage, page } = toPaginator(pagination);

    return pageBounds(itemCount, itemsPerPage, page);
}
