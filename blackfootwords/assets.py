from pathlib import Path

from clld.web.assets import environment

import blackfootwords


environment.append_path(
    Path(blackfootwords.__file__).parent.joinpath('static').as_posix(),
    url='/blackfootwords:static/')
environment.load_path = list(reversed(environment.load_path))
