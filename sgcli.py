import curses
from curses.ascii import (isalnum,
                          BS,
                          DEL,
                          ESC,
                          SP)
import datetime
import json
import os
import random
import threading
import time

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
    stdscr.keypad(1)
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)

    home(stdscr)

def centered(win, y, message, *args):
    win.addstr(y, (WIDTH - len(message)) / 2, message, *args)


def search(stdscr, input=""):
    stdscr.clear()
    stdscr.border()
    centered(stdscr, 2, "Enter a performer, event or venue:")
    curses.curs_set(2)

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


def loading_thread(screen, ev, message):
    dots = []
    while not ev.is_set():
        dots.append([1, random.randint(1, WIDTH - 2), "."])
        dots.append([1, random.randint(1, WIDTH - 2), "*"])

        screen.clear()
        screen.border()

        for dot in dots:
            screen.addstr(dot[0], dot[1], dot[2])
            dot[0] += 1
        max_y = screen.getmaxyx()[0]
        dots = [d for d in dots if d[0] < max_y - 1]

        centered(screen, 12, message)
        screen.refresh()
        ev.wait(0.1)


def loading(screen, message="Loading..."):
    ev = threading.Event()
    t = threading.Thread(target=loading_thread, args=(screen, ev, message))
    t.start()
    return ev


def search_results(stdscr, query):
    t = loading(stdscr)
    # TODO error handling
    res = json.loads(requests.get("http://api.seatgeek.com/2/events?per_page=100&q=" + query).text)
    time.sleep(1)
    t.set()

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
    if dt.hour == 3 and dt.minute == 30:
        time_str = pad("Time TBD", 10, True)
    else:
        time_str = pad(dt.strftime("%I:%M %p"), 10, True)

    scr.addstr(4 + 2 * row, 2, date_str, attrs)
    scr.addstr(5 + 2 * row, 2, time_str, attrs)
    scr.addstr(4 + 2 * row, 13, pad(event["title"], 65), attrs)
    byline = "  " + event["venue"]["name"]
    state = event["venue"]["state"]
    if not state or event["venue"]["country"] != "US":
        state = event["venue"]["country"]
    byline += " - " + event["venue"]["city"] + ", " + state
    scr.addstr(5 + 2 * row, 13, pad(byline, 65), attrs)


PER_PAGE = 10
DOWN_KEYS = (ord("n"), ord("k"), curses.KEY_DOWN, 14) # 14 is ^n
UP_KEYS = (ord("p"), ord("j"), curses.KEY_UP, 16) # 16 is ^p
LEFT_KEYS = (ord("b"), ord("h"), curses.KEY_LEFT, 2) # 2 is ^b
RIGHT_KEYS = (ord("f"), ord("l"), curses.KEY_RIGHT, 6) # 6 is ^f

def results_page(stdscr, query, events, page_number, result_number):
    stdscr.clear()
    stdscr.border()

    max_page = (len(events) - 1) / PER_PAGE
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
        elif ev in (BS, DEL):
            return search(stdscr, query)
        elif ev in DOWN_KEYS:
            if (result_number < PER_PAGE - 1) and (PER_PAGE * page_number + result_number < len(events) - 1):
                result_number += 1
            elif page_number < max_page:
                result_number = 0
                page_number += 1
            return results_page(stdscr, query, events, page_number, result_number)
        elif ev in UP_KEYS:
            if result_number > 0:
                result_number -= 1
            elif page_number > 0:
                result_number = PER_PAGE - 1
                page_number -= 1
            return results_page(stdscr, query, events, page_number, result_number)
        elif ev in RIGHT_KEYS:
            if page_number < max_page:
                page_number += 1
            if (PER_PAGE * page_number + result_number > len(events) - 1):
                result_number = len(events) - 1 - PER_PAGE * page_number
            return results_page(stdscr, query, events, page_number, result_number)
        elif ev in LEFT_KEYS:
            if page_number > 0:
                page_number -= 1
            return results_page(stdscr, query, events, page_number, result_number)
        elif ev == ord("\n"):
            return event_page(stdscr, query, events, page_number, result_number)


def event_page(screen, query, events, page_number, result_number):
    event = events[PER_PAGE * page_number + result_number]

    t = loading(screen, "Searching the web's ticket sites...")
    # TODO error handling
    res = json.loads(requests.get("http://seatgeek.com/event/listings?id=%d" % event["id"]).text)
    t.set()

    listings = res["listings"]

    screen.clear()
    screen.border()

    centered(screen, 1, event["title"])

    dt = datetime.datetime.strptime(event["datetime_local"], "%Y-%m-%dT%H:%M:%S")
    if dt.hour == 3 and dt.minute == 30:
        time_str = "Time TBD"
    else:
        time_str = dt.strftime("%I:%M %p")
    date_str = dt.strftime("%%a %%b %d" % dt.day) + ", " + time_str
    byline = date_str + " - " + event["venue"]["name"]
    state = event["venue"]["state"]
    if not state or event["venue"]["country"] != "US":
        state = event["venue"]["country"]
    byline += ", " + state
    centered(screen, 2, byline)

    # max_page = (len(listings) - 1) / PER_PAGE
    # if page_number > max_page or page_number < 0:
    #     raise Exception("Bad page # %s" % page_number)

    # centered(stdscr, 2, "Search results for '%s' (%s/%s)" % (query, page_number + 1, max_page + 1))

    # i = 0
    # for event in events[page_number * PER_PAGE:(page_number + 1) * PER_PAGE]:
    #     draw_event(stdscr, event, i, i == result_number)
    #     i += 1

    screen.refresh()

    while True:
        ev = screen.getch()
        if ev in (ord("q"), ESC):
            return quit(screen)
        elif ev == ord("s"):
            return search(screen)
        elif ev == ord("h"):
            return home(screen)
        elif ev in (BS, DEL):
            return results_page(screen, query, events, page_number, result_number)


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


def quit(stdscr, message=None):
    stdscr.clear()
    draw_logo(stdscr)
    centered(stdscr, 19, "Seat you later!")
    if message:
        centered(stdscr, 20, message)
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
#        else: # DEBUG FIND KEY CODES
#            return quit(stdscr, repr(ev))


if __name__ == "__main__":
    os.environ["TERM"] = "xterm"
    curses.wrapper(main)
