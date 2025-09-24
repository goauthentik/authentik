"""merge utils"""

from deepmerge import Merger  # type: ignore[attr-defined]

MERGE_LIST_UNIQUE = Merger(
    [(list, ["append_unique"]), (dict, ["merge"]), (set, ["union"])], ["override"], ["override"]
)
