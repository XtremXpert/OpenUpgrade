# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import importlib.util
import os

from openupgradelib import openupgrade


def _access_conversion():
    path = os.path.join(os.path.dirname(__file__), "access_conversion.py")
    spec = importlib.util.spec_from_file_location("access_conversion", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@openupgrade.migrate()
def migrate(env, version):
    # the custom group rules restricting the permissions of the other
    # modules, and the validation of the converted domains
    _access_conversion().convert(env, final=True)
    openupgrade.disable_invalid_filters(env)
