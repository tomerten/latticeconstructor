# -*- coding: utf-8 -*-

"""
Module latticeconstructor.parse 
=================================================================

A module

"""

from typing import Tuple, Union

from latticejson.convert import FROM_ELEGANT, TO_MADX
from latticejson.parse import parse_elegant, parse_madx

_CONVERSION_DICT = {
    "KQUAD": "QUADRUPOLE",
    "KSEXT": "SEXTUPOLE",
    "DRIF": "DRIFT",
    "RFCA": "RFCAVITY",
    "CSBEND": "SBEND",
    "MONI": "MONITOR",
    "WATCH": "MARKER",
    "EVKICK": "VKICKER",
    "EHKICK": "HKICKER",
    "MARK": "MARKER",
}


def parse_from_string(string: str, ftype: str = "lte") -> Tuple[Union[str, None], dict, list]:
    """Method to parse an elegant lattice string to name, defintions and ordered
    lattice element list.

    Parameters
    ----------
    string : str
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Lattice string.

    ftype: optional, str, default = 'lte'
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    format type

    Returns
    -------
    Tuple[Union[str,None],dict, list]
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    name, element definitions dict, element ordered list

    """
    assert ftype.lower() in ["lte", "madx"]

    # use latticejson parser
    if ftype == "lte":
        latdata = parse_elegant(string)
    else:
        latdata = parse_madx(string)

    # create command dict for later use
    cdict = {}
    for command in latdata.get("commands"):
        try:
            cdict[command[0]] = command[1] if len(command[1]) == 1 else list(command[1])
        except Exception:
            cdict[command[0]] = ""

    # get the element definitions dict
    definitions = latdata.get("elements", [])

    # convert to madx names
    definitions = {}
    for name, (_type, attributes) in latdata.get("elements", []).items():
        madtype = _type.upper()
        if ftype == "lte":
            # if no matching type make a marker
            try:
                madtype = TO_MADX[FROM_ELEGANT[_type.lower()]].upper()
            except Exception:
                madtype = _CONVERSION_DICT[_type.upper()]

        definitions[name.upper()] = {
            **{"family": madtype},
            **{k.upper(): v for k, v in attributes.items()},
        }

    # get the lattice sub-lattice dicts
    lattice = latdata.get("lattices", [])

    # method to flatten the sublattices
    def flatten(sublat_dict):
        def _walker(k, lattices=sublat_dict):
            for child in lattices[k]:
                if child in lattices:
                    yield from _walker(child)
                else:
                    yield child

        return _walker(list(sublat_dict.keys())[-1])

    # load ordered list to lattice
    # TODO: requested madx sequence lark parser to be merged in main branch so the
    # hack below can be avoided
    if bool(lattice):
        lattice = list(flatten(lattice))
        lattice = [el.upper() for el in lattice]
    else:
        cdict.pop("ENDSEQUENCE")
        lattice = [el.upper() for el in list(cdict.keys())]

    # attempt to load lattice name
    lattice_name = cdict.get("use", None)

    return lattice_name, definitions, lattice
