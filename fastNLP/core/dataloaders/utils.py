from typing import Callable
import inspect
import ast

from ..log import logger
from ..utils.cache_results import get_func_calls, truncate_start_blanks
__all__ = [
    "indice_collate_wrapper"
]


def indice_collate_wrapper(func:Callable):
    """
    其功能是封装一层collate_fn,将dataset取到的tuple数据分离开，将idx打包为indices。

    :param func: 需要修饰的函数
    :return:
    """
    if hasattr(func, '__name__') and func.__name__ == '_indice_collate_wrapper':  # 如果已经被包裹过了
       return func

    def _indice_collate_wrapper(tuple_data):  # 这里不能使用 functools.wraps ，否则会检测不到
        indice, ins_list = [], []
        for idx, ins in tuple_data:
            indice.append(idx)
            ins_list.append(ins)
        return indice, func(ins_list)
    _indice_collate_wrapper.__wrapped__ = func  # 记录对应的

    return _indice_collate_wrapper


def _match_param(fun, call_fn:Callable, fn_name:str=None):
    """
    在调用 _match_param 的函数(就是 fun )中会调用 call_fn 这个函数。由于 fun 中支持的函数比 call_fn 更多，例如低版本的
       :class:`~.fastNLP.TorchDataLoader` 中支持的参数，在torch 1.6 版本的 DataLoader 就不支持，但在高版本的 torch 中是支持的
       因此，这里需要根据当前版本的 DataLoader 判定出适合传入 DataLoader 进行初始化的参数，并且在不支持但又被设置的参数上进行
       warning 。

    :param fun: 调用函数本身
    :param call_fn:
    :param fn_name: 方便报错的用的函数
    :return:
    """
    try:
        if fn_name is None:
            try:
                fn_name = call_fn.__name__
            except:
                fn_name = str(call_fn)

        last_frame = inspect.currentframe().f_back

        # 调用 _match_param 的函数名称，获取默认的参数值
        fun_default_params = {}
        fun_parameters = inspect.signature(fun)
        for name, fun_param in fun_parameters.parameters.items():
            if fun_param.default is not fun_param.empty:
                fun_default_params[name] = fun_param.default

        # 获取实际传入的参数值
        param_names, args_name, kwargs_name, values = inspect.getargvalues(last_frame)
        if args_name is not None:
            raise RuntimeError("Function does not support positional arguments, such as: fun(*args).")
        kwargs = values.get(kwargs_name, {})
        for param in param_names:
            if param not in values:
                value = fun_default_params.get(param)
            else:
                value = values[param]
            kwargs[param] = value

        # 根据需要实际需要调用的 call_fn 的参数进行匹配
        call_fn_parameters = inspect.signature(call_fn)
        call_fn_kwargs = {}
        has_kwargs = False
        for name, param in call_fn_parameters.parameters.items():
            if name == 'self':
                continue
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):  # 最前面的 args
                call_fn_kwargs[name] = param.default
            if param.kind == param.VAR_KEYWORD:
                has_kwargs = True

        # 组装得到最终的参数
        call_kwargs = {}
        for name, value in kwargs.items():
            if name in call_fn_kwargs or has_kwargs:  # 如果存在在里面，或者包含了 kwargs 就直接运行
                call_kwargs[name] = value
            # 如果不在需要调用的函数里面，同时又是非默认值
            elif name not in call_fn_kwargs and name in fun_default_params and fun_default_params[name]!=value:
                logger.rank_zero_warning(f"Parameter:{name} is not supported for {fn_name}.")

        return call_kwargs
    except BaseException as e:
        logger.debug(f"Exception happens when match parameters for {fn_name}: {e}")
        return None

if __name__ == '__main__':
    def demo(*args, **kwargs):
        pass

    d = indice_collate_wrapper(demo)

    print(d.__name__)
    print(d.__wrapped__)