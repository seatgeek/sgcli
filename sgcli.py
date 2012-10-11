import curses
from curses.ascii import (ESC)
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


def draw_search(stdscr):
    stdscr.clear()
    stdscr.addstr(2, 10, "SEARCH:")
    stdscr.refresh()


def draw_home(stdscr, message=None):
    stdscr.clear()

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

    if message:
        stdscr.addstr(20, (WIDTH - len(message)) / 2, message)

    stdscr.refresh()


if __name__ == "__main__":
    os.environ["TERM"] = "xterm"
    curses.wrapper(main)
