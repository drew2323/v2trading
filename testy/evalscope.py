# def my_function():
#     return "Hello, World!"


# def call_function_by_name():
#     func_name = "my_function"
#     # Use eval to call the function
#     result = eval(func_name)()

def my_function():
    return "Hello, World!"


def call_function_by_name():
    # Create a closure to capture the my_function function
    def inner_function():
        return eval("my_function")()

    result = inner_function()
    return result


print(call_function_by_name())