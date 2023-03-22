
import functools

def debug_args(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        outputs = f"{func.__name__}("
        for i, arg in enumerate(args, 1):
            outputs += f"{arg}, "
        for key, value in kwargs.items():
            outputs += f"{key}': {value}, "
        outputs += ")"
        print(outputs)

        return func(*args, **kwargs)

    return wrapper
