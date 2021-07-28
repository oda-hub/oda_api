colors_enabled = True

if colors_enabled:
    RED = "\033[31m"
    GREEN = "\033[32m"
    BROWN = "\033[33m"
    BLUE = "\033[34m"
    PURPLE = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[37m"
    GREY = "\033[37m"
    YELLOW = "\033[33m"
    NC = "\033[0m"

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    RC = "\033[7m"
else:
    # set all
    NC = ""
