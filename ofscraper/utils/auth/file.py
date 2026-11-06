r"""
                                                             
 _______  _______         _______  _______  _______  _______  _______  _______  _______ 
(  ___  )(  ____ \       (  ____ \(  ____ \(  ____ )(  ___  )(  ____ )(  ____ \(  ____ )
| (   ) || (    \/       | (    \/| (    \/| (    )|| (   ) || (    )|| (    \/| (    )|
| |   | || (__     _____ | (_____ | |      | (____)|| (___) || (____)|| (__    | (____)|
| |   | ||  __)   (_____)(_____  )| |      |     __)|  ___  ||  _____)|  __)   |     __)
| |   | || (                   ) || |      | (\ (   | (   ) || (      | (      | (\ (   
| (___) || )             /\____) || (____/\| ) \ \__| )   ( || )      | (____/\| ) \ \__
(_______)|/              \_______)(_______/|/   \__/|/     \||/       (_______/|/   \__/
                                                                                      
"""

import json
import os
import logging

from rich.console import Console

import ofscraper.utils.auth.make as make
import ofscraper.utils.auth.schema as auth_schema
import ofscraper.utils.auth.utils.error as auth_error
import ofscraper.utils.auth.utils.dict as auth_dict
import ofscraper.utils.paths.common as common_paths
console = Console()


def read_auth():
    """
    Reads and validates the auth file, handling errors interactively.
    Returns the auth dictionary
    """
    while True:
        try:
            # Attempt to get the auth data
            old_auth = auth_dict.get_auth_dict()
            auth = auth_schema.auth_schema(old_auth)

            # Perform normal logic checks
            if auth_schema.auth_key_missing(old_auth):
                auth = write_auth(auth)
            if auth_schema.auth_key_null(auth):
                auth,_ = make.make_auth(auth)
            
            # If all checks pass, break the loop and return the auth data
            break

        except (FileNotFoundError, json.JSONDecodeError) as e:
            result = auth_error.handle_auth_errors(e)
            if result =="quit":
                logging.getLogger("shared").info("unable to read auth file")
                quit()
    return auth


def edit_auth():
    """
    Opens the auth editing menu, handling errors interactively.
    Returns the new auth dictionary or a command string ('quit', 'main').
    """
    while True:
        try:
            auth_dict.get_auth_dict()           
            break
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Delegate error handling
            result = auth_error.handle_auth_errors(e,include_main_menu=True)
            if result in {"quit", "main"}:
                return result
    
    current_auth = auth_dict.get_auth_dict()
    new_auth,result = make.make_auth(current_auth, include_main_menu=True)
    
    # Check if the user quit from the edit menu itself
    if result in {"quit", "main"}:
        return result

    console.print("Your `auth.json` file has been edited.")
    return new_auth


def write_auth(auth):
    if isinstance(auth, dict):
        auth = json.dumps(auth, indent=4)
    p = str(common_paths.get_auth_file())
    dirpath = os.path.dirname(p) or '.'
    tmp_path = os.path.join(dirpath, '.auth_tmp')
    # Atomic write: temp file in same dir -> os.replace, mode 0600
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(auth)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    os.replace(tmp_path, p)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    return auth_dict.get_auth_dict(auth)
