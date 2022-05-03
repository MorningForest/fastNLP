__all__ = [
    'NumpyNumberPadder',
    'NumpySequencePadder',
    "NumpyTensorPadder"
]

from numbers import Number
from abc import ABC
from typing import Any, Union
import numpy as np

from .padder import Padder
from .utils import get_padded_numpy_array, is_number_or_numpy_number
from .exceptions import *


def _get_dtype(ele_dtype, dtype, class_name):
    if ele_dtype is not None and not is_number_or_numpy_number(ele_dtype):
        raise EleDtypeUnsupportedError(f"`{class_name}` only supports padding python numbers "
                                       f"or numpy numbers but get `{ele_dtype}`.")

    if dtype is None:
        dtype = ele_dtype
    else:
        if not is_number_or_numpy_number(dtype):
            raise DtypeUnsupportedError(f"The dtype of `{class_name}` only supports python numbers "
                                        f"or numpy numbers but get `{dtype}`.")
        dtype = dtype
    return dtype


class NumpyNumberPadder(Padder):
    def __init__(self, pad_val=0, ele_dtype=None, dtype=None):
        """
        可以将形如 [1, 2, 3] 这类的数据转为 np.array([1, 2, 3])

        :param pad_val: 该值无意义
        :param ele_dtype: 用于检测当前 field 的元素类型是否可以转换为 np.array 类型。
        :param dtype: 输出的数据的 dtype 是什么
        """
        dtype = _get_dtype(ele_dtype, dtype, self.__class__.__name__)
        super().__init__(pad_val=pad_val, dtype=dtype)

    @staticmethod
    def pad(batch_field, pad_val, dtype):
        return np.array(batch_field, dtype=dtype)


class NumpySequencePadder(Padder):
    def __init__(self, pad_val=0, ele_dtype=None, dtype=None):
        """
        将类似于 [[1], [1, 2]] 的内容 pad 为 np.array([[1, 0], [1, 2]]) 可以 pad 多重嵌套的数据。

        :param pad_val: pad 的值是多少。
        :param ele_dtype: 用于检测当前 field 的元素类型是否可以转换为 np.array 类型。
        :param dtype: 输出的数据的 dtype 是什么
        """
        dtype = _get_dtype(ele_dtype, dtype, self.__class__.__name__)
        super().__init__(pad_val=pad_val, dtype=dtype)

    @staticmethod
    def pad(batch_field, pad_val, dtype):
        return get_padded_numpy_array(batch_field, dtype=dtype, pad_val=pad_val)


class NumpyTensorPadder(Padder):
    def __init__(self, pad_val=0, ele_dtype=None, dtype=None):
        """
        pad 类似于 [np.array([3, 4], np.array([1])] 的 field

        :param pad_val: pad 的值是多少。
        :param ele_dtype: 用于检测当前 field 的元素类型是否可以转换为 np.array 类型。
        :param dtype: 输出的数据的 dtype 是什么
        """
        dtype = _get_dtype(ele_dtype, dtype, self.__class__.__name__)
        super().__init__(pad_val=pad_val, dtype=dtype)

    @staticmethod
    def pad(batch_field, pad_val, dtype):
        shapes = [field.shape for field in batch_field]
        max_shape = [len(batch_field)] + [max(*_) for _ in zip(*shapes)]
        array = np.full(max_shape, fill_value=pad_val, dtype=dtype)
        for i, field in enumerate(batch_field):
            slices = (i, ) + tuple(slice(0, s) for s in shapes[i])
            array[slices] = field
        return array
