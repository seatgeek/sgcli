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
import subprocess
import threading
import time
import webbrowser

import requests


# TODO presentation, maps, autocomplete, packaging, oauth/columbus?


WIDTH = 80
HEIGHT = 25
PER_PAGE = 10


def addstr(win, y, x, s, *args):
#    return win.addstr(y, x, "".join([curses.unctrl(c) for c in s]), *args)
    return win.addstr(y, x, s, *args)


def main(stdscr):
    global WIDTH
    global HEIGHT
    global PER_PAGE
    global PER_PAGE_2

    HEIGHT, WIDTH = stdscr.getmaxyx()
    PER_PAGE = (HEIGHT - 4) / 3
    PER_PAGE_2 = (HEIGHT - 5) / 2

    stdscr.keypad(1)
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

    home(stdscr)


def centered(win, y, message, *args):
    addstr(win, y, int((WIDTH - len(message)) / 2), message, *args)


def search(stdscr, input=""):
    stdscr.clear()
    stdscr.border()
    centered(stdscr, 2, "Enter a performer, event or venue:")
    curses.curs_set(2)

    while True:
        # Search bar
        addstr(stdscr, 4, WIDTH / 2 - 20, "_" * 40, curses.A_DIM);
        addstr(stdscr, 4, WIDTH / 2 - 20, input);

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
            addstr(screen, dot[0], dot[1], dot[2])
            dot[0] += 1
        dots = [d for d in dots if d[0] < HEIGHT - 1]

        centered(screen, 12, message)
        screen.refresh()
        ev.wait(0.1)


def loading(screen, message="Loading..."):
    ev = threading.Event()
    t = threading.Thread(target=loading_thread, args=(screen, ev, message))
    t.start()
    return (ev, t)


def search_results(stdscr, query):
    (ev, t) = loading(stdscr)
    # TODO error handling
    res = json.loads(requests.get("http://api.seatgeek.com/2/events?per_page=100&q=" + query).text)
    ev.set()
    t.join()

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

    addstr(scr, 4 + 3 * row, 2, date_str, attrs)
    addstr(scr, 5 + 3 * row, 2, time_str, attrs)
    addstr(scr, 4 + 3 * row, 13, pad(event["title"], WIDTH - 15), attrs)
    byline = "  " + event["venue"]["name"]
    state = event["venue"]["state"]
    if not state or event["venue"]["country"] != "US":
        state = event["venue"]["country"]
    byline += " - " + event["venue"]["city"] + ", " + state
    addstr(scr, 5 + 3 * row, 13, pad(byline, WIDTH - 15), attrs)


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
        if ev == ord("q"):
            return confirm_quit(stdscr)
        elif ev == ESC:
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
        elif ev in UP_KEYS:
            if result_number > 0:
                result_number -= 1
            elif page_number > 0:
                result_number = PER_PAGE - 1
                page_number -= 1
        elif ev in RIGHT_KEYS:
            if page_number < max_page:
                page_number += 1
            if (PER_PAGE * page_number + result_number > len(events) - 1):
                result_number = len(events) - 1 - PER_PAGE * page_number
        elif ev in LEFT_KEYS:
            if page_number > 0:
                page_number -= 1
        elif ev == ord("\n"):
            return event_page(stdscr, query, events, page_number, result_number)
        return results_page(stdscr, query, events, page_number, result_number)


def draw_event_header(screen, event):
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


def event_page(screen, query, events, page_number, result_number):
    event = events[PER_PAGE * page_number + result_number]

    (ev, t) = loading(screen, "Searching the web's ticket sites...")
    # TODO error handling
    res = json.loads(requests.get("http://seatgeek.com/event/listings?id=%d" % event["id"]).text)
    ev.set()
    t.join()

    listings = res["listings"]
    if not listings:
        draw_event_header(screen, event)
        centered(screen, 4, "Shoot. No listings found :(. Here's a bunny.")
        centered(screen, 6, "                          +MM0^            ")
        centered(screen, 7, "                           +MMMM1          ")
        centered(screen, 8, "                           0MMNMM+         ")
        centered(screen, 9, "                           +MMMNNN         ")
        centered(screen, 10, "              ^^++++^^      1MMM0N1++^     ")
        centered(screen, 11, "         +1o00000o00000oooo1+oMM000MM00o^  ")
        centered(screen, 12, "       10000o000000000oo000oo00MNNMMMM000+ ")
        centered(screen, 13, "     o000oo0o00o0000o0000000o0000MMMMN0000+")
        centered(screen, 14, "   +0000000000000000oo000000000000NNN0000N0")
        centered(screen, 15, "  +000000NMMMMMNN00000000000000NN00000000o^")
        centered(screen, 16, "  0000MMMMMMMMMMMMMN00000000000MMNNMo1+^^  ")
        centered(screen, 17, "  0000MMMMMN000000NNNo000000000NMM1+       ")
        centered(screen, 18, "  100000000000000000NN00ooo000001^         ")
        centered(screen, 19, " 1o0000o00000000000000N000000N+            ")
        centered(screen, 20, "NMMMM0o00000000000000000000MM0             ")
        centered(screen, 21, "+o0MMMoo000000000000000000NNMNo1^          ")
        centered(screen, 22, "      ^o000000000o000ooooo0000NM0          ")
        centered(screen, 24, "(h) home  (s) search  (q) quit  (BKSP) back")

        screen.refresh()

        while True:
            ev = screen.getch()
            if ev == ord("q"):
                return confirm_quit(screen)
            elif ev == ESC:
                return quit(screen)
            elif ev == ord("s"):
                return search(screen)
            elif ev == ord("h"):
                return home(screen)
            elif ev in (BS, DEL):
                return results_page(screen, query, events, page_number, result_number)

    listings = grouped(listings)
    previous_args = [screen, query, events, page_number, result_number]
    return listings_page(previous_args, screen, event, listings, 0, 0)


def grouped(listings):
    grouped = {}
    for l in listings:
        key = l.get("mk") or "%s_%s" % (l["s"], l["r"])
        # TODO if quantity has been filtered use that instead
        key += "--%s" % l["q"]
        if key not in grouped:
            grouped[key] = l
    return sorted(grouped.values(), key=lambda x: x["dq"], reverse=True)


def draw_listing(screen, listing, row, highlight):
    attrs = 0
    if highlight:
        attrs = curses.A_REVERSE
    elif listing["b"] in (0, 1):
        attrs = curses.color_pair(2)
    elif listing["b"] == 2:
        attrs = curses.color_pair(4)
    else:
        attrs = curses.color_pair(5)

    addstr(screen, 5 + 2 * row, 2, " " * (WIDTH - 4), attrs)
    addstr(screen, 5 + 2 * row, 3, "(%d)" % listing["dq"], attrs)
    addstr(screen, 5 + 2 * row, 8, (listing["s"] + " - row " + listing["r"]).title(), attrs)
    addstr(screen, 5 + 2 * row, WIDTH - 15, pad(str(listing["q"]), 2, True) + pad((listing["et"] and " etix" or " tix"), 7), attrs)
    addstr(screen, 5 + 2 * row, WIDTH - 7, pad("$" + str(listing["pf"]), 4, True), attrs)


def listings_page(previous_args, screen, event, listings, page_number, result_number):
    max_page = (len(listings) - 1) / PER_PAGE_2
    if page_number > max_page or page_number < 0:
        raise Exception("Bad page # %s" % page_number)

    draw_event_header(screen, event)
    centered(screen, 3, "(%s/%s)" % (page_number + 1, max_page + 1))

    current_listing = None
    i = 0
    for listing in listings[page_number * PER_PAGE_2:(page_number + 1) * PER_PAGE_2]:
        if i == result_number:
            current_listing = listing
        draw_listing(screen, listing, i, i == result_number)
        i += 1

    screen.refresh()

    while True:
        ev = screen.getch()
        if ev == ord("q"):
            return confirm_quit(screen)
        elif ev == ESC:
            return quit(screen)
        elif ev == ord("s"):
            return search(screen)
        elif ev == ord("h"):
            return home(screen)
        elif ev in (BS, DEL):
            return results_page(*previous_args)
        elif ev in DOWN_KEYS:
            if (result_number < PER_PAGE_2 - 1) and (PER_PAGE_2 * page_number + result_number < len(listings) - 1):
                result_number += 1
            elif page_number < max_page:
                result_number = 0
                page_number += 1
        elif ev in UP_KEYS:
            if result_number > 0:
                result_number -= 1
            elif page_number > 0:
                result_number = PER_PAGE_2 - 1
                page_number -= 1
        elif ev in RIGHT_KEYS:
            if page_number < max_page:
                page_number += 1
            if (PER_PAGE_2 * page_number + result_number > len(listings) - 1):
                result_number = len(listings) - 1 - PER_PAGE_2 * page_number
        elif ev in LEFT_KEYS:
            if page_number > 0:
                page_number -= 1
        elif ev == ord("\n"):
            previous_args = [previous_args, screen, event, listings, page_number, result_number]
            return listing_page(previous_args, screen, event, current_listing)
        return listings_page(previous_args, screen, event, listings, page_number, result_number)


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def listing_page(previous_args, screen, event, listing):
    map_image = None
    ga = False
    no_map = False

    if event.get("general_admission"):
        ga = True
    else:
        map_image = "http://seatgeek.com/event/static_map_image?width=320&height=320&event_id=%s&section=%s" % (event["id"], listing["s"])

        (ev, t) = loading(screen)
        # TODO error handling
        res = requests.get(map_image)
        ev.set()
        t.join()

    draw_event_header(screen, event)
    centered(screen, 4, "%s tickets in Section %s, Row %s" % (listing["q"],
                                                              listing["s"].title(),
                                                              listing["r"].title()))
    centered(screen, 5, "$%s base + $%s fees & shipping = $%s each. (b)uy on %s" % (listing["p"], listing["pf"] - listing["p"], listing["pf"], listing["m"]))
    if listing["d"]:
        centered(screen, 6, listing["d"][:WIDTH-2])

    if ga:
        centered(screen, 12, "General Admission Show")
        centered(screen, 13, "This show does not have assigned seating.")
    elif no_map:
        centered(screen, 12, "Seating Chart Unavailable")
    else:
        pass

    screen.refresh()

    link = "http://seatgeek.com/event/click/?tid=%s&eid=%s&section=%s&row=%s&quantity=%s&price=%s&baseprice=%s&market=%s&sg=0&dq=%s" % (listing["id"], event["id"], listing["s"], listing["r"], listing["q"], listing["pf"], listing["p"], listing["m"], listing["dq"])

    while True:
        ev = screen.getch()
        if ev == ord("q"):
            return confirm_quit(screen)
        elif ev == ESC:
            return quit(screen)
        elif ev == ord("s"):
            return search(screen)
        elif ev == ord("h"):
            return home(screen)
        elif ev in (BS, DEL):
            return listings_page(*previous_args)
        elif ev in (ord("b"), ord("w")):
            browse(link, ev == ord("b"))
            return post_purchase(screen, previous_args)


def post_purchase(screen, previous_args):
    screen.nodelay(True)

    dots = []
    i = 0

    while True:
        i += 1
        dots.append([random.randint(1, HEIGHT - 2), WIDTH - 2, random.random() < 0.5 and "+" or "o"])

        screen.clear()
        screen.border()

        for dot in dots:
            addstr(screen, dot[0], dot[1], dot[2])
            dot[1] -= 1
            if random.random() < 0.1:
                dot[2] = dot[2] == "+" and "o" or "+"
        dots = [d for d in dots if d[1] > 1]

        trail_length = (WIDTH - 10) / 4
        screen.addstr(10, 2, (i % 4 < 2 and "-_" or "_-") * trail_length, curses.color_pair(5))
        screen.addstr(11, 2, (i % 4 < 2 and "-_" or "_-") * trail_length, curses.color_pair(4))
        screen.addstr(12, 2, (i % 4 < 2 and "-_" or "_-") * trail_length, curses.color_pair(2))
        screen.addstr(13, 2, (i % 4 < 2 and "-_" or "_-") * trail_length, curses.color_pair(1))
        screen.addstr(10, 2 + trail_length * 2, ",------,")
        screen.addstr(11, 2 + trail_length * 2, "|   /\\_/\\")
        screen.addstr(12, 2 + trail_length * 2, "|__( ^ .^)")
        screen.addstr(13, 4 - (i % 3) + trail_length * 2, "\"\"  \"\"")
        screen.addstr(11 + (i % 6 / 3), 1 + trail_length * 2, "~")

        centered(screen, 5, "Thanks for using SeatGeek! Enjoy the event!")
        centered(screen, 6, "(BKSP) back  (s) search  (h) home  (q) quit")
        screen.refresh()

        ev = screen.getch()
        if ev == ord("q"):
            screen.nodelay(False)
            return confirm_quit(screen)
        elif ev == ESC:
            screen.nodelay(False)
            return quit(screen)
        elif ev == ord("s"):
            screen.nodelay(False)
            return search(screen)
        elif ev == ord("h"):
            screen.nodelay(False)
            return home(screen)
        elif ev in (BS, DEL):
            screen.nodelay(False)
            return listings_page(*previous_args)

        time.sleep(0.1)


def draw_logo(stdscr):
    x = (WIDTH - 50) / 2
    addstr(stdscr, 2, x, " ;;;;               ;   ", curses.color_pair(1))
    addstr(stdscr, 3, x, "::                  ;   ", curses.color_pair(1))
    addstr(stdscr, 4, x, ";,     .;;:  :;;;  ;;;; ", curses.color_pair(1))
    addstr(stdscr, 5, x, "`;:    ;  ;` `  ;,  ;   ", curses.color_pair(1))
    addstr(stdscr, 6, x, "  ,;: ,;::;,    :,  ;   ", curses.color_pair(1))
    addstr(stdscr, 7, x, "    ; :,     ,;,:,  ;   ", curses.color_pair(1))
    addstr(stdscr, 8, x, "    ; ,;     ;  ;,  ;`  ", curses.color_pair(1))
    addstr(stdscr, 9, x, ",:,;,  ;:,:` ;,:,:. ;;, ", curses.color_pair(1))
    addstr(stdscr, 10, x, " ..     `.`   .  `   .` ", curses.color_pair(1))

    addstr(stdscr, 1, x + 24, "                    :;,   ")
    addstr(stdscr, 2, x + 24, "  ;;;;;              :,   ")
    addstr(stdscr, 3, x + 24, " ;.                  :,   ")
    addstr(stdscr, 4, x + 24, "::       ,;;,  `;;;  :, ,;")
    addstr(stdscr, 5, x + 24, ";`      .;  ;  ;  :, :,`; ")
    addstr(stdscr, 6, x + 24, ";     ; ;;::;..;::;; ::;  ")
    addstr(stdscr, 7, x + 24, ";.    ; ;.    ,;     ::;  ")
    addstr(stdscr, 8, x + 24, ".;    ; ::    .;     :,,; ")
    addstr(stdscr, 9, x + 24, " :;;:;;  ;:,:  ;;,:. :, ;:")
    addstr(stdscr, 10, x + 24, "   ..`    `.    `.`  `   `")
    addstr(stdscr, 11, x + 24, "      `              ,    ")
    addstr(stdscr, 12, x + 24, "     :;;            ,;    ")
    addstr(stdscr, 13, x + 24, "       ,;          :;     ")
    addstr(stdscr, 14, x + 24, "        `;,      .;:      ")
    addstr(stdscr, 15, x + 24, "          ,;;;;;;;        ")


def confirm_quit(screen):
    screen.clear()
    screen.border()
    draw_logo(screen)
    centered(screen, 19, "ONE DOES NOT SIMPLY")
    centered(screen, 20, "QUIT SEATGEEK")
    centered(screen, 24, "Quit? (y/n)")
    screen.refresh()

    while True:
        ev = screen.getch()
        if ev == ord("y"):
            return quit(screen)
        elif ev == ord("n"):
            return home(screen)


def quit(stdscr, message=None):
    stdscr.clear()
    draw_logo(stdscr)
    centered(stdscr, 19, "Seat you later!")
    if message:
        centered(stdscr, 20, message)
    stdscr.refresh()


def browse(uri, prefer_links=True):
    links = which("links") or which("elinks") or which("lynx")
    if prefer_links and links:
        subprocess.call([links, uri])
    else:
        webbrowser.open(uri)


def home(stdscr):
    stdscr.clear()
    stdscr.border()
    draw_logo(stdscr)
    centered(stdscr, 19, "Welcome to SeatGeek!")
    centered(stdscr, 20, "(s) search  (q/ESC) quit")
    stdscr.refresh()

    while True:
        ev = stdscr.getch()
        if ev == ord("q"):
            return confirm_quit(stdscr)
        elif ev == ESC:
            return quit(stdscr)
        elif ev == ord("s"):
            return search(stdscr)
        elif ev == ord("t"):
            return post_purchase(stdscr, [])
        elif ev == ord("a"):
            return listing_page([], stdscr, {u'stats': {u'listing_count': 6644, u'average_price': 321.94, u'lowest_price': 46.0, u'highest_price': 12102.0}, u'links': [], u'performers': [{u'home_team': True, u'name': u'New York Yankees', u'short_name': u'Yankees', u'url': u'http://seatgeek.com/new-york-yankees-tickets/', u'image': u'http://cdn.seatgeek.com/images/performers/8/new-york-yankees-1a4323/huge.jpg', u'primary': True, u'id': 8, u'score': 0.81294999999999995, u'images': {u'small': u'http://cdn.seatgeek.com/images/performers/8/new-york-yankees-777201/small.jpg', u'huge': u'http://cdn.seatgeek.com/images/performers/8/new-york-yankees-1a4323/huge.jpg', u'large': u'http://cdn.seatgeek.com/images/performers/8/new-york-yankees-a5647b/large.jpg'}, u'type': u'mlb', u'slug': u'new-york-yankees'}], u'url': u'http://seatgeek.com/tbd-yankees-tickets/10-14-2012-bronx-new-york-yankee-stadium/mlb/1022833/', u'datetime_local': u'2012-10-14T03:30:00', u'title': u'ALCS: TBD at New York Yankees - Home Game 2', u'venue': {u'city': u'Bronx', u'extended_address': None, u'links': [], u'url': u'http://seatgeek.com/yankee-stadium-seating-chart/', u'country': u'US', u'id': 8, u'state': u'NY', u'score': 0.93030000000000002, u'postal_code': u'10452', u'location': {u'lat': 40.827800000000003, u'lon': -73.927599999999998}, u'address': u'1 East 161st Street', u'slug': u'yankee-stadium', u'name': u'Yankee Stadium'}, u'datetime_tbd': True, u'short_title': u'ALCS: TBD at New York Yankees - Home Game 2', u'datetime_utc': u'2012-10-14T07:30:00', u'score': 0.85823000000000005, u'taxonomies': [{u'parent_id': None, u'id': 1000000, u'name': u'sports'}, {u'parent_id': 1000000, u'id': 1010000, u'name': u'baseball'}, {u'parent_id': 1010000, u'id': 1010100, u'name': u'mlb'}], u'type': u'mlb', u'id': 1022833}, {u'sp': [2, 4], u'd': u'This is Cafe Seating: you will be seated at bar stools with a drink rail. These tickets are available for email delivery', u'f': 50.5, u'pu': 0, u'm': u'razorgator', u'mk': None, u'sh': 4.2374999999999998, u'q': 4, u'p': 202, u's': u'field 118', u'r': u'28 s', u'pf': 257, u'pk': 0, u'et': 1, u'b': 1, u'sg': u"We don't recognize the row listed for this ticket, so we're displaying it in the last row of this section.", u'id': u'mT301STq%2fd43oJj98rbhAUtCy0sKzYyl', u'dq': 82})
        elif ev == ord("b"):
            return listing_page([], stdscr, {"stats":{"listing_count":14,"average_price":70.43,"lowest_price":37,"highest_price":108},"links":[],"title":"Other Lives with Indians","url":"http://seatgeek.com/other-lives-with-indians-tickets/new-york-new-york-bowery-ballroom-2012-11-28-8-pm/concert/934747/","type":"concert","performers":[{"short_name":"Other Lives","url":"http://seatgeek.com/other-lives-tickets/","image":"http://cdn.seatgeek.com/images/performers/9736/other-lives-2b22f2/huge.jpg","primary":True,"slug":"other-lives","score":0.69347,"images":{"huge":"http://cdn.seatgeek.com/images/performers/9736/other-lives-2b22f2/huge.jpg"},"type":"band","id":9736,"name":"Other Lives"},{"short_name":"Indians","url":"http://seatgeek.com/indians-tickets/","image":None,"slug":"indians","score":0,"images":[],"type":"band","id":24934,"name":"Indians"}],"venue":{"city":"New York","extended_address":None,"links":[],"url":"http://seatgeek.com/bowery-ballroom-seating-chart/","country":"US","slug":"bowery-ballroom","state":"NY","score":0.54747,"postal_code":"10002","location":{"lat":40.72,"lon":-73.99},"address":"6 Delancey Street","id":719,"name":"Bowery Ballroom"},"short_title":"Other Lives with Indians","general_admission":True,"datetime_utc":"2012-11-29T01:00:00","score":0.63996,"datetime_local":"2012-11-28T20:00:00","taxonomies":[{"parent_id":None,"id":2000000,"name":"concert"}],"datetime_tbd":False,"id":934747}, {u'sp': [2, 4], u'd': u'This is Cafe Seating: you will be seated at bar stools with a drink rail. These tickets are available for email delivery', u'f': 50.5, u'pu': 0, u'm': u'razorgator', u'mk': None, u'sh': 4.2374999999999998, u'q': 4, u'p': 202, u's': u'field 118', u'r': u'28 s', u'pf': 257, u'pk': 0, u'et': 1, u'b': 1, u'sg': u"We don't recognize the row listed for this ticket, so we're displaying it in the last row of this section.", u'id': u'mT301STq%2fd43oJj98rbhAUtCy0sKzYyl', u'dq': 82})
        elif ev == ord("c"):
            return listing_page([], stdscr, {"stats":{"listing_count":None,"average_price":None,"lowest_price":None,"highest_price":None},"links":[],"title":"Jon McLaughlin","url":"http://seatgeek.com/jon-mclaughlin-tickets/northampton-massachusetts-iron-horse-music-hall-2012-10-16-3-30-am/concert/998449/","type":"concert","performers":[{"short_name":"Jon McLaughlin","url":"http://seatgeek.com/jon-mclaughlin-tickets/","image":"http://cdn.seatgeek.com/images/performers/991/jon-mclaughlin-c6da68/huge.jpg","primary":True,"slug":"jon-mclaughlin","score":0.29364,"images":{"small":"http://cdn.seatgeek.com/images/performers/991/jon-mclaughlin-a8be17/small.jpg","huge":"http://cdn.seatgeek.com/images/performers/991/jon-mclaughlin-c6da68/huge.jpg","large":"http://cdn.seatgeek.com/images/performers/991/jon-mclaughlin-d631fd/large.jpg","medium":"http://cdn.seatgeek.com/images/performers/991/jon-mclaughlin-f13c65/medium.jpg"},"type":"band","id":991,"name":"Jon McLaughlin"}],"venue":{"city":"Northampton","extended_address":None,"links":[],"url":"http://seatgeek.com/iron-horse-music-hall-seating-chart/","country":"US","slug":"iron-horse-music-hall","state":"MA","score":0,"postal_code":"01060","location":{"lat":42.32,"lon":-72.63},"address":"20 Center Street","id":2155,"name":"Iron Horse Music Hall"},"short_title":"Jon McLaughlin","datetime_utc":"2012-10-16T07:30:00","score":0.27034,"datetime_local":"2012-10-16T03:30:00","taxonomies":[{"parent_id":None,"id":2000000,"name":"concert"}],"datetime_tbd":False,"id":998449}, {u'sp': [2, 4], u'd': u'This is Cafe Seating: you will be seated at bar stools with a drink rail. These tickets are available for email delivery', u'f': 50.5, u'pu': 0, u'm': u'razorgator', u'mk': None, u'sh': 4.2374999999999998, u'q': 4, u'p': 202, u's': u'field 118', u'r': u'28 s', u'pf': 257, u'pk': 0, u'et': 1, u'b': 1, u'sg': u"We don't recognize the row listed for this ticket, so we're displaying it in the last row of this section.", u'id': u'mT301STq%2fd43oJj98rbhAUtCy0sKzYyl', u'dq': 82})
#        else: # DEBUG FIND KEY CODES
#            return quit(stdscr, repr(ev))


if __name__ == "__main__":
    os.environ["TERM"] = "xterm"
    curses.wrapper(main)
