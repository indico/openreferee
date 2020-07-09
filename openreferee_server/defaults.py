from . import __version__


SERVICE_INFO = {"version": __version__, "name": "OpenReferee Reference Implementation"}
DEFAULT_TAGS = {
    "ERR_WRONG_TITLE": {"title": "Wrong Title", "color": "red", "system": False},
    "ERR_SILLY_TITLE": {"title": "Silly Title", "color": "orange", "system": False},
    "OK_TITLE": {"title": "Title OK", "color": "green", "system": False},
    "WATERMARKED": {"title": "Watermarked", "color": "brown", "system": True},
}
DEFAULT_EDITABLES = {"paper", "poster"}
DEFAULT_FILE_TYPES = {
    "paper": [
        {
            "name": "PDF",
            "extensions": ["pdf"],
            "allow_multiple_files": False,
            "required": True,
            "publishable": True,
            "filename_template": "{code}_paper",
        },
        {
            "name": "Source Files",
            "extensions": ["tex", "doc"],
            "allow_multiple_files": True,
            "required": True,
            "publishable": False,
        },
    ],
    "poster": [
        {
            "name": "PDF",
            "extensions": ["pdf"],
            "allow_multiple_files": False,
            "required": True,
            "publishable": True,
            "filename_template": "{code}_poster",
        },
        {
            "name": "Source Files",
            "extensions": ["ai", "svg"],
            "allow_multiple_files": False,
            "required": True,
            "publishable": False,
        },
    ],
}
