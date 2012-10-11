import curses
from curses.ascii import (isalnum,
                          BS,
                          DEL,
                          ESC,
                          SP)
import datetime
import json
import os

import requests


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

    home(stdscr)

def centered(win, y, message, *args):
    win.addstr(y, (WIDTH - len(message)) / 2, message, *args)


def search(stdscr):
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
            curses.curs_set(0)
            return home(stdscr)
        elif ev == ord("\n"):
            curses.curs_set(0)
            return search_results(stdscr, input)
        elif isalnum(ev):
            input += chr(ev)

    stdscr.refresh()


def search_results(stdscr, query):
    stdscr.clear()
    stdscr.border()
    centered(stdscr, 2, "Search results for '%s'" % query)
    centered(stdscr, 4, "Loading...")
    stdscr.refresh()

    # TODO error handling
    res = json.loads(requests.get("http://api.seatgeek.com/2/events?per_page=100&q=" + query).text)

    events = res.get("events", [])
    if not events:
        stdscr.clear()
        stdscr.border()
        centered(stdscr, 2, "Search results for '%s'" % query)
        centered(stdscr, 4, "No results :( - any key to search again")
        stdscr.getch()
        return search(stdscr)

    return results_page(stdscr, query, events, 0, 0)


def pad(s, l, left=False):
    if len(s) > l:
        return s[:l]
    if left:
        return " " * (l - len(s)) + s
    return s + " " * (l - len(s))


def draw_event(scr, event, row, highlight):
    attrs = 0
    if highlight:
        attrs = curses.A_REVERSE

    dt = datetime.datetime.strptime(event["datetime_local"], "%Y-%m-%dT%H:%M:%S")
    date_str = pad(dt.strftime("%%a %%b %d" % dt.day), 10)
    time_str = pad(dt.strftime("%I:%M %p"), 10, True)

    scr.addstr(4 + 2 * row, 2, date_str, attrs)
    scr.addstr(5 + 2 * row, 2, time_str, attrs)
    scr.addstr(4 + 2 * row, 13, pad(event["title"], 65), attrs)
    byline = "  " + event["venue"]["name"] + " - " + event["venue"]["city"] + ", " + event["venue"]["state"]
    scr.addstr(5 + 2 * row, 13, pad(byline, 65), attrs)


PER_PAGE = 10
def results_page(stdscr, query, events, page_number, result_number):
    stdscr.clear()
    stdscr.border()

    max_page = len(events) / PER_PAGE
    if page_number > max_page or page_number < 0:
        raise Exception("Bad page # %s" % page_number)

    centered(stdscr, 2, "Search results for '%s' (%s/%s)" % (query, page_number + 1, max_page + 1))

    i = 0
    for event in events[page_number * PER_PAGE:(page_number + 1) * PER_PAGE]:
        draw_event(stdscr, event, i, i == result_number)
        i += 1

    stdscr.refresh()

    while True:
        ev = stdscr.getch()
        if ev in (ord("q"), ESC):
            return quit(stdscr)
        elif ev == ord("s"):
            return search(stdscr)
        elif ev == ord("h"):
            return home(stdscr)
        elif ev in (ord("n"), curses.KEY_DOWN):
            if (result_number < PER_PAGE - 1) and (PER_PAGE * page_number + result_number < len(events) - 1):
                result_number += 1
            elif page_number < max_page:
                result_number = 0
                page_number += 1
            return results_page(stdscr, query, events, page_number, result_number)
        elif ev in (ord("p"), curses.KEY_DOWN):
            if result_number > 0:
                result_number -= 1
            elif page_number > 0:
                result_number = PER_PAGE - 1
                page_number -= 1
            return results_page(stdscr, query, events, page_number, result_number)


def draw_logo(stdscr):
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


def quit(stdscr):
    stdscr.clear()
    stdscr.border()
    draw_logo(stdscr)
    centered(stdscr, 19, "Seat you later!")
    stdscr.refresh()


def home(stdscr):
    stdscr.clear()
    stdscr.border()
    draw_logo(stdscr)
    centered(stdscr, 19, "Welcome to SeatGeek!")
    centered(stdscr, 20, "(s) search  (q/ESC) quit")
    stdscr.refresh()

    while True:
        ev = stdscr.getch()
        if ev in (ord("q"), ESC):
            return quit(stdscr)
        elif ev == ord("s"):
            return search(stdscr)


if __name__ == "__main__":
    os.environ["TERM"] = "xterm"
    curses.wrapper(main)
