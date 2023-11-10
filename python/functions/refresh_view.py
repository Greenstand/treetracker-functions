
def hello(who):
    assert who != "world", "Please don't greet the world"
    print(f"Hello, {who}!")
    return f"Hello, {who}!"
