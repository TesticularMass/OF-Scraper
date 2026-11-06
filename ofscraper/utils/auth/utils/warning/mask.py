# Session secrets; showing them in full would leak the login if the output is shared.
SECRET_KEYS = {"sess", "x-bc", "auth_uid", "auth_uid_"}


def mask_secret(value):
    text = str(value or "")
    if len(text) <= 8:
        return "*" * len(text)
    return f"{'*' * 8}{text[-4:]}"
