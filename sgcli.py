import curses
from curses.ascii import (isalnum,
                          BS,
                          DEL,
                          ESC,
                          SP)
import curses.textpad
import os


# MAIN_WINDOW = 0
# RECOMMENDATIONS = 1
# SEARCH = 2
# EVENT_SEARCH = 3
# PERFORMER_SEARCH = 4
# VENUE_SEARCH = 5
# BROWSE NFL, etc


WIDTH = 80


def main(stdscr):
    stdscr.keypad(0)
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)

    draw_home(stdscr)

    while True:
        ev = stdscr.getch()
        if ev in (ord("q"), ESC):
            draw_home(stdscr, "Seat you later!")
            break
        elif ev == ord("h"):
            draw_home(stdscr)
        elif ev == ord("s"):
            draw_search(stdscr)


def centered(win, y, message, *args):
    win.addstr(y, (WIDTH - len(message)) / 2, message, *args)


def draw_search(stdscr):
    stdscr.clear()
    stdscr.border()
    centered(stdscr, 2, "Enter a performer, event or venue:")
    curses.curs_set(2)

    input = ""

    while True:
        # Search bar
        stdscr.addstr(4, WIDTH / 2 - 20, "_" * 40, curses.A_DIM);
        stdscr.addstr(4, WIDTH / 2 - 20, input);

        ev = stdscr.getch()
        if ev == SP:
            input += " "
        if ev in (BS, DEL):
            input = input[:-1]
        elif ev == ESC:
            return draw_home(stdscr)
        elif isalnum(ev):
            input += chr(ev)

    stdscr.refresh()


def draw_home(stdscr, message=None):
    stdscr.clear()
    stdscr.border()

    x = (WIDTH - 50) / 2
    stdscr.addstr(2, x, " ;;;;               ;   ", curses.color_pair(1))
    stdscr.addstr(3, x, "::                  ;   ", curses.color_pair(1))
    stdscr.addstr(4, x, ";,     .;;:  :;;;  ;;;; ", curses.color_pair(1))
    stdscr.addstr(5, x, "`;:    ;  ;` `  ;,  ;   ", curses.color_pair(1))
    stdscr.addstr(6, x, "  ,;: ,;::;,    :,  ;   ", curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(7, x, "    ; :,     ,;,:,  ;   ", curses.color_pair(1))
    stdscr.addstr(8, x, "    ; ,;     ;  ;,  ;`  ", curses.color_pair(1))
    stdscr.addstr(9, x, ",:,;,  ;:,:` ;,:,:. ;;, ", curses.color_pair(1))
    stdscr.addstr(10, x, " ..     `.`   .  `   .` ", curses.color_pair(1))

    stdscr.addstr(1, x + 24, "                    :;,   ")
    stdscr.addstr(2, x + 24, "  ;;;;;              :,   ")
    stdscr.addstr(3, x + 24, " ;.                  :,   ")
    stdscr.addstr(4, x + 24, "::       ,;;,  `;;;  :, ,;")
    stdscr.addstr(5, x + 24, ";`      .;  ;  ;  :, :,`; ")
    stdscr.addstr(6, x + 24, ";     ; ;;::;..;::;; ::;  ")
    stdscr.addstr(7, x + 24, ";.    ; ;.    ,;     ::;  ")
    stdscr.addstr(8, x + 24, ".;    ; ::    .;     :,,; ")
    stdscr.addstr(9, x + 24, " :;;:;;  ;:,:  ;;,:. :, ;:")
    stdscr.addstr(10, x + 24, "   ..`    `.    `.`  `   `")
    stdscr.addstr(11, x + 24, "      `              ,    ")
    stdscr.addstr(12, x + 24, "     :;;            ,;    ")
    stdscr.addstr(13, x + 24, "       ,;          :;     ")
    stdscr.addstr(14, x + 24, "        `;,      .;:      ")
    stdscr.addstr(15, x + 24, "          ,;;;;;;;        ")

    message_2 = None
    if not message:
        message = "Welcome to SeatGeek!"
        message_2 = "(h) home  (s) search  (q/ESC) quit"

    centered(stdscr, 19, message)
    if message_2:
        centered(stdscr, 20, message_2)

    stdscr.refresh()


if __name__ == "__main__":
    os.environ["TERM"] = "xterm"
    curses.wrapper(main)
