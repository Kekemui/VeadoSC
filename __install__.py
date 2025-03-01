from os.path import abspath, dirname, join

from streamcontroller_plugin_tools.installation_helpers import create_venv

toplevel = dirname(abspath(__file__))
create_venv(join(toplevel, "backend", ".venv"), join(toplevel, "backend", "requirements.txt"))
