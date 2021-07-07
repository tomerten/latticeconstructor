# -*- coding: utf-8 -*-

"""
Module latticeconstructor.core 
=================================================================

A module containing the main lattice builder classes.

"""

import queue

# your imports here ...
import re
from copy import deepcopy
from typing import List, Union

import pandas as pd

from .parse import parse_from_string


class LatticeBuilderLine:
    """Class for building lattice tables"""

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

    def __init__(self):
        self.lattice = []
        self.definitions = {}
        self.table = None
        self.positions = None

        # roll back queue
        self.history = queue.LifoQueue()

    def add_def(self, _def: Union[dict, List[dict]]) -> None:
        """Add definitions dictionary to the definitions

        Parameters:
        -----------
        _def	: List[dict] | dict
                        list of dicts or dict containing element definitions

        """
        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # length can not be zero - necessary for pos calc
        assert list(_def.values())[0].get("L", None) is not None

        # update names
        for k, v in _def.items():
            _def[k]["name"] = v.get("name", k)

        # update definitions dicts
        self.definitions = {**self.definitions, **_def}

        # convert to madx element types
        for d in self.definitions.keys():
            self.definitions[d]["family"] = self._CONVERSION_DICT.get(
                self.definitions[d]["family"], self.definitions[d]["family"]
            )

        # attempt update table
        if not self.table is None:
            self._update_table()

    def add_element(self, element: str) -> None:
        """Add element to the lattice at the end

        Parameters:
        -----------
        element:	str
                element name
        """
        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # make a list
        if not isinstance(element, list):
            element = [element]

        # add element at end of lattice
        self.lattice = self.lattice + element

        # update table
        self._update_table()

    def replace_element(self, old, new, **kwargs):
        """Replace element by name or idx, give idx in kwargs to select by idx method.

        Parameters:
        -----------
        old :   str
            name of old element

        new :   str
            name of new element or a list of elements

        idx :   int, optional
            index of old element
        """
        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # make list
        if not isinstance(new, list):
            new = [new]

        # select between idx or name replacement
        if "idx" in kwargs:
            idx = kwargs.get("idx")
            self.lattice = self.lattice[:idx] + new + self.lattice[idx + 1 :]
        else:
            idx = [k for k in self.lattice].index(old)
            self.lattice = self.lattice[:idx] + new + self.lattice[idx + 1 :]

        # update table
        self._update_table()

    def replace_list(self, start_idx: int, end_idx: int, new: Union[List[str], str]) -> None:
        """Replace a series of elements in the lattice

        Parameters:
        -----------
        start_idx : int
            start index of series to remove
        end_idx   : int
            end index of series to remove
        new       : List[str], str
            replacement element or list of replacement elements
        """
        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # make list
        if not isinstance(new, list):
            new = [new]

        # update lattice and table
        self.lattice = self.lattice[:start_idx] + new + self.lattice[end_idx + 1 :]
        self._update_table()

    def insert_element_before(self, element: str, idx_next: int) -> None:
        """Insert elements before a given element, by idx only.

        Parameters:
        -----------
        element : str
            name of the element to insert
        idx_next: int
            index of the element to insert before
        """
        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # if single element given tranform into list to insert
        if not isinstance(element, list):
            element = [element]

        # insert and update table
        self.lattice = self.lattice[:idx_next] + element + self.lattice[idx_next:]
        self._update_table()

    def insert_element_after(self, element: str, idx_prev: int) -> None:
        """Insert elements after a given element, by idx only.

        Parameters:
        -----------
        element : str
            name of the element to insert
        idx_next: int
            index of the element to insert after
        """

        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # if single element given tranform into list to insert
        if not isinstance(element, list):
            element = [element]

        # insert and update table
        self.lattice = self.lattice[: idx_prev + 1] + element + self.lattice[idx_prev + 1 :]
        self._update_table()

    def remove_element(self, elem_idx: int) -> None:
        """Remove element by idx

        Parameters:
        -----------
        elem_idx : int
            index of element to remove
        """
        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # remove and update table
        self.lattice = self.lattice[:elem_idx] + self.lattice[elem_idx + 1 :]
        self._update_table()

    def remove_from_to(self, start_idx: int, end_idx: int) -> None:
        """Remove series of elements between start_idx and end_idx
        (elements at these idxs are also removed!)

        Parameters:
        -----------
        start_idx : int
            start index for removal
        end_idx : int
            end index for removal
        """
        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # remove elements and update table
        self.lattice = self.lattice[:start_idx] + self.lattice[end_idx + 1 :]
        self._update_table()

    def get_idx(self, elem: str) -> List[int]:
        """Get a list of idx corresponding to given element name

        Parameters:
        -----------
        elem : str
            element name to get indices for
        """
        return [i for i, n in enumerate(self.lattice) if n == elem]

    def build_table(self):
        """Manually build table."""
        # roll back
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )
        self._update_table()

    def _update_table(self):
        """Callback called after any change to update table."""
        # roll back
        # self.history.put(
        #    (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        # )

        # only build/update table if all elements are defined
        # otherwise print error message and print list of missing defintions
        if all([k in self.definitions.keys() for k in self.lattice]):
            temp = [{**self.definitions[k], **{"name": k}} for k in self.lattice]
            ntable = pd.DataFrame(temp)
            if self.positions is not None:
                ntable["at"] = self.positions["at"]
                # ntable = pd.merge(ntable, self.positions, how="outer", on="name")
            else:
                ntable["at"] = ntable["L"].cumsum() - ntable["L"] / 2

            if ntable["L"].isnull().values.any():
                ntable.loc[ntable["L"].isnull(), "L"] = 0.0
                ntable["at"] = ntable["L"].cumsum() - ntable["L"] / 2

            self.table = ntable
        else:
            print("Table not updated - not all elements defined.")
            print(set(self.lattice) - self.definitions.keys())

    # ------------------------------
    # more advanced methods
    # ------------------------------
    def load_from_file(self, filename: str, ftype: str = "lte") -> None:
        """Method to load a lattice from file (uses latticejson).

        Parameters
        ----------
        filename : str
            filename
        ftype : str, optional
            format type ['lte'|'madx'], by default "lte"
        """
        # save previous state to history
        self.history.put(
            (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
        )

        # check if ftype is ok
        assert ftype in ["lte", "madx"]

        # read the string from file
        with open(filename, "r") as f:
            latstr = f.read()

        # use parser based on latticejson
        name, pos, defs, lat = parse_from_string(latstr, ftype=ftype)

        # update the instance
        self.definitions = defs
        self.lattice = lat
        self.positions = pos

        if name is not None:
            self.name = name

    def undo(self):
        """Undo previous change."""
        if not self.history.empty():
            old = self.history.get()
            self.definitions, self.lattice, self.table = old
        else:
            print("No previous states available")

    # def load_lattice_from_file(self, filename: str, ftype: str = "lte") -> None:
    #     """
    #     Method to load lattice from a lattice file.

    #     Parameters:
    #     -----------
    #     filename:    str
    #             lattice filename
    #     ftype   :    str
    #             one of lte, madx-line, madx-seq
    #     """
    #     self.history.put(
    #         (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
    #     )
    #     assert ftype in ["lte", "madx-line", "madx-seq"]

    #     with open(filename, "r") as f:
    #         latstr = f.read()

    #     if ftype != "madx-seq":
    #         # read line commands from filestr
    #         structures = re.findall(r"([^,\s?]+)\s*:\s*LINE\s*=\s*\(([^)]+)\)", latstr)

    #         # init
    #         sublat_dict = {}

    #         # add all line commands to dict
    #         for latname, latline in structures:
    #             sublat_dict[latname] = re.sub(r"\s+", "", latline).split(",")

    #         def flatten(sublat_dict):
    #             def _walker(k, lattices=sublat_dict):
    #                 for child in lattices[k]:
    #                     if child in lattices:
    #                         yield from _walker(child)
    #                     else:
    #                         yield child

    #             return _walker(list(sublat_dict.keys())[-1])

    #         # load ordered list to lattice
    #         self.lattice = list(flatten(sublat_dict))
    #     else:
    #         self.lattice = [s.strip() for s in re.findall(r"(.*)\s*,\s*at", latstr)]

    # def load_definitions_from_file(self, filename: str, ftype: str = "lte") -> None:
    #     """
    #     Method to load element defintions from lattice file.

    #     Parameters:
    #     -----------
    #     filename:    str
    #             lattice filename
    #     ftype   :    str
    #             one of lte, madx-line, madx-seq
    #     """
    #     self.history.put(
    #         (deepcopy(self.definitions), deepcopy(self.lattice), deepcopy(self.table))
    #     )
    #     assert ftype in ["lte", "madx-line", "madx-seq"]

    #     with open(filename, "r") as f:
    #         latstr = f.read()

    #     if ftype != "madx-seq":
    #         #             _defs = re.findall(r"(.*): ([^,\s]+)\s*[,\s*(.*)]+",latstr)
    #         _defs = re.findall(r"(\w+)\s*:\s*(\w+)\s*[,;](.*)", latstr)
    #         #             print(_defs)
    #         if ftype == "lte":
    #             settings = dict([(t[1], t[0]) for t in re.findall("%(.*) sto (.*)", latstr)])
    #         else:
    #             settings = dict(
    #                 [
    #                     (t[1], t[0])
    #                     for t in re.findall(
    #                         r"(?:CONST)?\s+(\w+[\.]\w+)\s*[:]*=\s*([+-]?[0-9]*[.]?[0-9]+);", latstr
    #                     )
    #                 ]
    #             )

    #             def flattenValues(entry):
    #                 def _walker(k, settings=settings):
    #                     for child in settings[k]:
    #                         if child in settings:
    #                             yield from _walker(child)
    #                         else:
    #                             yield float(child)

    #                 return _walker(entry)

    #             for k in settings.keys():
    #                 settings[k] = flattenValues(k)

    #         self.definitions = self._clean_def(_defs, settings)
    #     else:
    #         #             _defs = re.findall(r"(.*): ([^,\s]+)\s*[,\s*(.*)]+",latstr)
    #         _defs = re.findall(r"(\w+)\s*:\s*(\w+)\s*[,;](.*)", latstr)
    #         settings = dict(
    #             [
    #                 (t[1], t[0])
    #                 for t in re.findall(
    #                     r"(?:CONST)?\s+(\w+[\.]\w+)\s*[:]*=\s*([+-]?[0-9]*[.]?[0-9]+);", latstr
    #                 )
    #             ]
    #         )

    #         def flattenValues(entry):
    #             def _walker(k, settings=settings):
    #                 for child in settings[k]:
    #                     if child in settings:
    #                         yield from _walker(child)
    #                     else:
    #                         yield float(child)

    #             return _walker(entry)

    #         for k in settings.keys():
    #             settings[k] = flattenValues(k)

    #         self.definitions = self._clean_def(_defs, settings)

    # def _clean_def(self, re_defs, settings):
    #     """Method to internally clean up the element definitions.

    #     Parameters:
    #     -----------
    #     re_defs:
    #         list of tuples containing regex extracted defintions
    #     settings:   dict
    #         dictionary containing the regex extracted settings
    #     """
    #     # generate element definitions to push into the builder class
    #     out = {}
    #     for el in re_defs:
    #         row = {}

    #         # element name
    #         row["name"] = el[0]

    #         # convert or keep if not in conversion list
    #         row["family"] = self._CONVERSION_DICT.get(el[1], el[1])

    #         # we skip the non relevant
    #         if not row["family"] in self._CONVERSION_DICT.values():
    #             continue

    #         if row["family"] in ["MARKER", "MONITOR"]:
    #             if not "BPM" in el[0].upper():
    #                 row["family"] = "MARKER"
    #             row["L"] = 0.0
    #         else:
    #             try:
    #                 # add the arguments to the definition
    #                 for arg in el[2].split(","):
    #                     if arg[-1] == ";":
    #                         arg = arg[:-1]
    #                     k, v = arg.split("=")
    #                     if k[-1] == ":":
    #                         k = k[:-1]
    #                     k = k.strip()  # remove surrounding whitespace
    #                     v = v.strip()  # remove surrounding whitespace
    #                     try:
    #                         v = float(v)  # convert to float if possible
    #                     except:
    #                         try:
    #                             v = float(
    #                                 settings[v[1:-1]].strip()
    #                             )  # if string of powersupply get the value from the settings
    #                         except:
    #                             # special cases
    #                             if v.upper() == "TRUE":
    #                                 v = True
    #                             elif v.upper() == "FALSE":
    #                                 v = False

    #                     row[k.strip()] = v
    #             except:
    #                 # print failures and stop the conversion
    #                 print(el)
    #                 break

    #         _key = el[0].strip()  # remove surrounding whitespace
    #         row["name"] = _key
    #         out[_key] = row

    #     return out
