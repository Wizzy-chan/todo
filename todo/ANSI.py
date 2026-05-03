class ANSI:
    BLACK = "\x1b[0;30m"
    RED = "\x1b[0;31m"
    GREEN = "\x1b[0;32m"
    YELLOW = "\x1b[0;33m"
    BLUE = "\x1b[0;34m"
    PURPLE = "\x1b[0;35m"
    CYAN = "\x1b[0;36m"
    WHITE = "\x1b[0;37m"

    BLACK_BOLD = "\x1b[1;30m"
    RED_BOLD = "\x1b[1;31m"
    GREEN_BOLD = "\x1b[1;32m"
    YELLOW_BOLD = "\x1b[1;33m"
    BLUE_BOLD = "\x1b[1;34m"
    PURPLE_BOLD = "\x1b[1;35m"
    CYAN_BOLD = "\x1b[1;36m"
    WHITE_BOLD = "\x1b[1;37m"

    BLACK_UNDERLINE = "\x1b[4;30m"
    RED_UNDERLINE = "\x1b[4;31m"
    GREEN_UNDERLINE = "\x1b[4;32m"
    YELLOW_UNDERLINE = "\x1b[4;33m"
    BLUE_UNDERLINE = "\x1b[4;34m"
    PURPLE_UNDERLINE = "\x1b[4;35m"
    CYAN_UNDERLINE = "\x1b[4;36m"
    WHITE_UNDERLINE = "\x1b[4;37m"

    BG_BLACK = "\x1b[40m"
    BG_RED = "\x1b[41m"
    BG_GREEN = "\x1b[42m"
    BG_YELLOW = "\x1b[43m"
    BG_BLUE = "\x1b[44m"
    BG_PURPLE = "\x1b[45m"
    BG_CYAN = "\x1b[46m"
    BG_WHITE = "\x1b[47m"

    BLACK_BRIGHT = "\x1b[0;90m"
    RED_BRIGHT = "\x1b[0;91m"
    GREEN_BRIGHT = "\x1b[0;92m"
    YELLOW_BRIGHT = "\x1b[0;93m"
    BLUE_BRIGHT = "\x1b[0;94m"
    PURPLE_BRIGHT = "\x1b[0;95m"
    CYAN_BRIGHT = "\x1b[0;96m"
    WHITE_BRIGHT = "\x1b[0;97m"

    BLACK_BOLD_BRIGHT = "\x1b[1;90m"
    RED_BOLD_BRIGHT = "\x1b[1;91m"
    GREEN_BOLD_BRIGHT = "\x1b[1;92m"
    YELLOW_BOLD_BRIGHT = "\x1b[1;93m"
    BLUE_BOLD_BRIGHT = "\x1b[1;94m"
    PURPLE_BOLD_BRIGHT = "\x1b[1;95m"
    CYAN_BOLD_BRIGHT = "\x1b[1;96m"
    WHITE_BOLD_BRIGHT = "\x1b[1;97m"

    BG_BLACK_BRIGHT = "\x1b[0;100m"
    BG_RED_BRIGHT = "\x1b[0;101m"
    BG_GREEN_BRIGHT = "\x1b[0;102m"
    BG_YELLOW_BRIGHT = "\x1b[0;103m"
    BG_BLUE_BRIGHT = "\x1b[0;104m"
    BG_PURPLE_BRIGHT = "\x1b[0;105m"
    BG_CYAN_BRIGHT = "\x1b[0;106m"
    BG_WHITE_BRIGHT = "\x1b[0;107m"

    @staticmethod
    def RGB(r, g, b):
        return f"\x1b[38;2;{r};{g};{b}m"

    @staticmethod
    def BG_RGB(r, g, b):
        return f"\x1b[48;2;{r};{g};{b}m"

    RESET = "\x1b[0m"


def print_with_format(fmt: str, string: str):
    print(f"{fmt}{string}{ANSI.RESET}")
