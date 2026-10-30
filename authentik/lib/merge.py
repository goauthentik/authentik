"""merge utils"""

from deepmerge import Merger

MERGE_LIST_UNIQUE = Merger(
    [(list, ["append_unique"]), (dict, ["merge"]), (set, ["union"])], ["override"], ["override"]
)
MERGE_LIST_REPLACE = Merger(
    [(list, ["override"]), (dict, ["merge"]), (set, ["union"])], ["override"], ["override"]
)
