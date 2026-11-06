import filecmp
import logging
import os
import pathlib
import platform
import shutil
from collections.abc import Iterable

import ofscraper.commands.scraper.actions.utils.globals as common_globals
import ofscraper.utils.dates as dates
import ofscraper.utils.paths.common as common_paths
from ofscraper.commands.scraper.actions.utils.log import get_medialog
import ofscraper.utils.hash as hash_util

try:
    from win32_setctime import setctime  # pylint: disable=import-error
except ModuleNotFoundError:
    pass


def _same_content(a, b):
    """True when two paths are the same file (inode) or have identical bytes."""
    a, b = pathlib.Path(a), pathlib.Path(b)
    try:
        if a.stat().st_ino == b.stat().st_ino and a.stat().st_dev == b.stat().st_dev:
            return True
    except OSError:
        pass
    try:
        # shallow=False compares content, not just size/mtime
        return filecmp.cmp(str(a), str(b), shallow=False)
    except OSError:
        return False


def _disambiguate(path_to_file):
    """Return a path with _1, _2, … suffix that does not yet exist."""
    stem = path_to_file.stem
    suffix = path_to_file.suffix
    parent = path_to_file.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def moveHelper(temp, path_to_file, ele, log_=None):
    """Move temp to path_to_file, disambiguating when different media collide.

    Returns the path the file was actually written to so callers can record
    the real filename in the DB and apply mtimes to the right file.
    """
    log_ = log_ or logging.getLogger("shared")
    if not path_to_file.exists():
        shutil.move(temp, path_to_file)
        return path_to_file
    if _same_content(temp, path_to_file):
        # Same bytes (e.g. a retried download) - replace to refresh mtime
        shutil.move(temp, path_to_file)
        return path_to_file
    new_path = _disambiguate(path_to_file)
    log_.warning(
        f"{get_medialog(ele)} collision: {path_to_file.name} exists with different content, saving as {new_path.name}"
    )
    shutil.move(temp, new_path)
    hash_util.invalidate_hash(new_path)
    return new_path


def _resolve(path):
    path = pathlib.Path(path)
    try:
        return path.resolve()
    except OSError:
        # some network/virtual drives (e.g. WinError 1005 on mapped Windows
        # volumes) can't be resolved; these sets are only used to date
        # folders afterwards, so an absolute path is enough
        return path.absolute()


def _resolve_dir(path):
    path = _resolve(path)
    return path if path.is_dir() else path.parent


def addGlobalDir(path):
    # a str is iterable too, but it is one path
    paths = (
        [path]
        if isinstance(path, (str, os.PathLike)) or not isinstance(path, Iterable)
        else path
    )
    common_globals.dirSet.update(map(_resolve_dir, paths))


def addLocalDir(path):
    paths = [path] if not isinstance(path, list) else path
    common_globals.localDirSet.update(map(_resolve_dir, paths))


def set_time(path, timestamp):
    if platform.system() == "Windows":
        setctime(str(path), timestamp)
    os.utime(path, (timestamp, timestamp))


def setDirectoriesDate(dirSet=None, log=None):
    log = log or common_globals.log
    log.info("Setting Date for modified directories")
    output = set()
    # resolved the same way as the dir sets so is_relative_to compares like
    # with like (resolve() can turn a mapped drive letter into a UNC path)
    rootDir = _resolve(common_paths.get_save_location())
    
    # Use provided dirSet or fallback to global
    target_dirSet = dirSet if dirSet is not None else common_globals.dirSet
    log.debug(f"Original DirSet {list(target_dirSet)}")
    log.debug(f"rootDir {rootDir}")

    for ele in target_dirSet:
        output.add(ele)
        try:
            while not os.path.samefile(ele, rootDir) and not os.path.samefile(
                ele.parent, rootDir
            ):
                if ele.parent in output:
                    # We already added all subsequent paths in this tree
                    break
                if not pathlib.PurePath(ele.parent).is_relative_to(rootDir):
                    # Don't descend if the parent path is outside rootDir such as
                    # when a symlink was used somewhere in the path
                    break
                common_globals.log.debug(f"Setting Dates ele:{ele} rootDir:{rootDir}")
                output.add(ele.parent)
                ele = ele.parent
        except OSError as E:
            # samefile stats both paths, which fails on the same drives
            log.debug(f"could not walk up from {ele}: {E}")
    log.debug(f"Directories list {output}")
    for ele in output:
        try:
            set_time(ele, dates.get_current_time())
        except OSError as E:
            log.debug(f"could not set date on {ele}: {E}")
