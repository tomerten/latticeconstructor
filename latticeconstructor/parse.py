# -*- coding: utf-8 -*-

"""
Module latticeconstructor.parse 
=================================================================

A module

"""

from pathlib import Path
from typing import Tuple, Union

import pandas as pd
from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError
from latticejson.convert import FROM_ELEGANT, TO_MADX
from latticejson.parse import AbstractLatticeFileTransformer, ArithmeticTransformer, parse_elegant

BASE_DIR = Path(__file__).resolve().parent

with (BASE_DIR / "madx.lark").open() as file:
    MADX_PARSER = Lark(file, parser="lalr", maybe_placeholders=True)
    file.seek(0)
    ARITHMETIC_PARSER = Lark(file, parser="lalr", start="start_artih")


@v_args(inline=True)
class MADXTransformer(ArithmeticTransformer, AbstractLatticeFileTransformer):
    def sequence(self, name, *items):
        *attributes, elements = items
        self.lattices[name.upper()] = elements
        self.commands.append(("name", name))

    def seq_element(self, name, value):
        return name.upper(), value

    def seq_elements(self, *elements):
        return list(elements)


def parse_madx(string: str):
    tree = MADX_PARSER.parse(string)
    return MADXTransformer().transform(tree)


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

    ftype: optional, str, default = 'lte'

    Returns
    -------
    Tuple[Union[str,None],dict, list]

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
            cdict[command[0]] = command[1] if len(command) == 2 else list(command[1])
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
        if isinstance(lattice[0], tuple):
            positions = pd.DataFrame(lattice, columns=["name", "at"])
            lattice = [el[0].upper() for el in lattice]
            lattice_name = cdict["name"]
        else:
            positions = None
            lattice = [el.upper() for el in lattice]
            lattice_name = None
    else:
        cdict.pop("ENDSEQUENCE")
        lattice = [el.upper() for el in list(cdict.keys())]
        positions = [{k.upper(): float(v[1])} for k, v in cdict.items()]

    # attempt to load lattice name
    if ftype == "lte":
        lattice_name = cdict.get("use", None)

    return lattice_name, positions, definitions, lattice
