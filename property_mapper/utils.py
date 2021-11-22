from typing import Dict


def merge_dicts(src: Dict, dst: Dict, path: list = None, extend_lists: bool = False) -> Dict:
    if path is None:
        path = []

    for key in src:
        if key in dst:
            if isinstance(src[key], dict) and isinstance(dst[key], dict):
                merge_dicts(src=src[key], dst=dst[key], path=path + [str(key)], extend_lists=extend_lists)
            elif extend_lists and isinstance(src[key], (list, tuple)) and isinstance(dst[key], (list, tuple)):
                dst_list = list(dst[key])
                src_list = list(src[key])
                dst_list.extend(src_list)
                dst[key] = list(set(dst_list))
            else:
                dst[key] = src[key]
        else:
            dst[key] = src[key]

    return dst
