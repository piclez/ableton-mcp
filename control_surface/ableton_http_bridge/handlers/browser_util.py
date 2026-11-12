"""Shared helpers for locating loadable items in Live's browser by filename."""

from collections import deque

# Browser roots searched for samples, in priority order.
SAMPLE_ROOTS = ("user_library", "user_folders", "samples", "packs")


def _matches(item, filename):
    name = item.name.lower()
    return name == filename or name == filename.rsplit(".", 1)[0]


def _bfs(root, filename, max_depth=5):
    queue = deque([(root, 0)])
    while queue:
        item, depth = queue.popleft()
        try:
            if item.is_loadable and _matches(item, filename):
                return item
        except Exception:
            pass
        if depth < max_depth:
            try:
                for child in item.children:
                    queue.append((child, depth + 1))
            except Exception:
                pass
    return None


def find_sample(browser, path, max_depth=5):
    """Find a loadable browser item matching the basename of `path`.

    Matches on the full filename or its stem, case-insensitively, searching
    SAMPLE_ROOTS in order. Returns the browser item, or None if not found.
    """
    filename = path.split("/")[-1].lower()
    for root_name in SAMPLE_ROOTS:
        root = getattr(browser, root_name, None)
        if root is None:
            continue
        try:
            found = _bfs(root, filename, max_depth)
        except Exception:
            found = None
        if found:
            return found
    return None
