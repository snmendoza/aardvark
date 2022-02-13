# -*- coding: utf-8 -*-
""" Creats HDF5 file with various string types

    See: http://docs.h5py.org/en/latest/strings.html
"""

import sys

import h5py
import numpy as np


def make_special():
    """ Makes HDF-5 file with special cases
    """
    with h5py.File("special.hdf5", "w") as hdf:
        #Gives: AttributeError: 'module' object has no attribute 'Empty'
        ds_ints = hdf.create_dataset("emtpy attributes", (15,), dtype=int)
        ds_ints[:] = 15
        ds_ints.attrs["description"] = "A normal dataset with an empty attribute"
        ds_ints.attrs["empty attr"] = h5py.Empty("f")



def make_strings2():
    """ Makes HDF-5 file with string with Python 2

        Also this was made with h5py 2.x.

        See: https://docs.h5py.org/en/2.10.0/strings.html
             https://docs.h5py.org/en/2.10.0/special.html

        http://docs.h5py.org/en/latest/strings.html
             https://docs.h5py.org/en/3.2.1/special.html
    """
    assert sys.version_info[0] == 2, "Implemented for Python 2"
    assert int(h5py.__version__[0]) <= 2, "Implmented for h5py <= 2.x"

    with h5py.File("string2.h5", "w") as hdf:

        ds_ints = hdf.create_dataset("int dataset", (100,), dtype='i')
        ds_ints[0:4] = 52

        ds_fixed = hdf.create_dataset("fixed_len_ascii_ds", (100,), dtype="S10")
        ds_fixed[:] = 'Bill Gates from Microsoft'
        ds_fixed.attrs["description"] = "Fixed-length ASCII strings"
        ds_fixed.attrs["attr"] = np.string_("Hallo")

        dt_ascii = h5py.special_dtype(vlen=bytes)
        ds_var_ascii = hdf.create_dataset("var_len_ascii_ds", (100,), dtype=dt_ascii)
        ds_var_ascii[:] = 'Linus Thorvalds from Linux'
        ds_var_ascii.attrs["description"] = "Variables-length ASCII strings"
        ds_var_ascii.attrs["attr"] = b"Gegroet"

        scalar_var = hdf.create_dataset("var_len_ascii_scalar", tuple(), dtype=dt_ascii)
        scalar_var[tuple()] = 'Andrew Tanenbaum of the Vrije Universiteit'
        scalar_var.attrs["description"] = "Scalar of variable-length ASCII string"
        scalar_var.attrs["attr"] = b"Gegroet"

        dt_unicode = h5py.special_dtype(vlen=unicode)
        ds_var_unicode = hdf.create_dataset("var_len_unicode_ds", (100,), dtype=dt_unicode)
        ds_var_unicode[:] = "Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!"
        ds_var_unicode.attrs["description"] = "Variables-length Unicode strings"
        ds_var_unicode.attrs["attr"] =  u"a\xac\u1234\u20ac\U00008000"





def make_strings3():
    """ Makes HDF-5 file with string with Python 3 and h5py 3.x

        See: http://docs.h5py.org/en/latest/strings.html
             https://docs.h5py.org/en/3.2.1/special.html
    """
    assert sys.version_info[0] == 3, "Implemented for Python 3"
    assert int(h5py.__version__[0]) >= 3, "Implmented for h5py >= 3.x"

    from h5py import string_dtype

    with h5py.File("string3.h5", "w") as hdf:

        dataset = hdf.create_dataset("fixed_len_ascii", (100,), dtype=string_dtype(length=40))
        dataset[:] = 'Bill Gates from Microsoft'
        dataset.attrs["description"] = "Fixed-length ASCII strings"
        dataset.attrs["attr"] = np.string_("Hallo")
        dataset.attrs["empty attribute"] = h5py.Empty("f")

        dataset = hdf.create_dataset("fixed_len_utf-8", (100,), dtype=string_dtype(length=40, encoding="utf-8"))
        dataset[:] = 'Chào thế giới'
        dataset.attrs["description"] = "Fixed-length UTF-8 strings"
        dataset.attrs["attr"] = np.string_("Good bye")

        dataset = hdf.create_dataset("fixed_len_utf", (100,), dtype=string_dtype(length=None, encoding="utf-8"))
        dataset[:] = "Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!"
        dataset.attrs["description"] = "Variables-length Unicode strings"
        dataset.attrs["attr"] =  u"a\xac\u1234\u20ac\U00008000"

        scalar_var = hdf.create_dataset("var_len_ascii_scalar", tuple(), dtype=string_dtype(length=None, encoding="ascii"))
        scalar_var[tuple()] = 'Andrew Tanenbaum of the Vrije Universiteit'
        scalar_var.attrs["description"] = "Scalar of variable-length ASCII string"
        scalar_var.attrs["attr"] = b"Gegroet"

        # Arbitrary vlen data
        # https://docs.h5py.org/en/3.2.1/special.html#arbitrary-vlen-data
        # Note that Argos crashes at the moment when reading this.
        dataset = hdf.create_dataset("vlen_int", (100,), h5py.vlen_dtype(np.dtype('int32')))
        dataset[0] = [1,2,3]
        dataset[1] = [1,2,3,4,5]
        dataset.attrs["description"] = "Arbitrary length array of int (ragged array)"



if __name__ == '__main__':



    make_strings3()
    #make_special()

