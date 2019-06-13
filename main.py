import curses
from curses import ascii
import threading
import time
import systemd


service_list = []
manager = systemd.systemd()
thread_kill = 0
display = None
longest_name = 0
test_offset = 0
y = 0


def sort_services(val):
    return val.name.lower()


def update_service():
    while True:
        global test_offset, y
        start = test_offset
        stop = y + start
        if thread_kill == 1:
            exit(0)
        for i in range(start, stop):
            service_list[i].active_state = manager.get_active_state(service_list[i].name)
            service_list[i].enabled_state = manager.get_enabled_state(service_list[i].name)
        time.sleep(0.25)
        ''' sleep to lower CPU usage. Screen only refreshes every second so this sleep statement has
                              little to no negative effect on functionality of the program but lowers overall CPU usage '''


def update_active():
    while True:
        if thread_kill == 1:
            exit(0)
        for i in range(len(service_list)):
            service_list[i].active_state = manager.get_active_state(service_list[i].name)


def update_enabled():
    while True:
        if thread_kill == 1:
            exit(0)
        for i in range(len(service_list)):
            service_list[i].enabled_state = manager.get_enabled_state(service_list[i].name)


def parse_list():
    global longest_name
    result_list = manager.get_str_list_all()
    for name in result_list:
        if len(name)-8 > longest_name:
            longest_name = len(name)-8
        service = systemd.Service(name)
        service.description = manager.get_description(name)
        service.active_state = manager.get_active_state(name)
        service.enabled_state = manager.get_enabled_state(name)
        service_list.append(service)


class Display(object):

    def __init__(self):
        global y, x, test_offset
        self.stdscr = curses.initscr()
        y, x = self.stdscr.getmaxyx()
        self.stdscr.keypad(True)
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.selected = 0
        test_offset = 0
        curses.curs_set(0)
        self.bottom_bar = curses.newwin(1, x, y-1, 0)
        self.top_bar = curses.newwin(1, x, 0, 0)
        self.main_screen = curses.newwin(y-2, x, 1, 0)
        self.set_bars()
        y, x = self.main_screen.getmaxyx()

        try:
            curses.wrapper(self.loop)
        except KeyboardInterrupt:
            pass
        self.clean_up()

    def clean_up(self):  # sets terminal back to normal
        curses.nocbreak()
        curses.echo()
        self.stdscr.keypad(False)
        curses.curs_set(1)
        curses.endwin()

    def search(self):
        return

    def set_bars(self):
        global x, y
        self.bottom_bar.bkgd(' ', curses.A_REVERSE)
        self.bottom_bar.addstr(0, 0, "q-quit s-start x-stop r-restart e-enable d-disable", curses.A_REVERSE)
        self.top_bar.bkgd(' ', curses.A_REVERSE)
        self.top_bar.addstr(0, 0, "SERVICE", curses.A_REVERSE)
        self.top_bar.addstr(0, longest_name+4, "ACTIVE", curses.A_REVERSE)
        self.top_bar.addstr(0, longest_name+14, "ENABLED", curses.A_REVERSE)

    def refresh_display(self):
        global y, x, thread_kill, test_offset
        self.main_screen.erase()
        for i in range(y):
            if i == self.selected:
                self.main_screen.addstr(i, 0, service_list[i+test_offset].name[:-8], curses.A_REVERSE)
                self.main_screen.addstr(i, longest_name + 4, service_list[i+test_offset].active_state, curses.A_REVERSE)
                self.main_screen.addstr(i, longest_name + 14, service_list[i+test_offset].enabled_state, curses.A_REVERSE)
            else:
                self.main_screen.addstr(i, 0, service_list[i+test_offset].name[:-8], curses.color_pair(2))
                self.main_screen.addstr(i, longest_name + 4, service_list[i+test_offset].active_state, curses.color_pair(2))
                self.main_screen.addstr(i, longest_name + 14, service_list[i+test_offset].enabled_state, curses.color_pair(2))

        self.top_bar.refresh()
        self.bottom_bar.refresh()
        self.main_screen.refresh()

    def loop(self, s):
        global y, x, thread_kill, test_offset
        while True:
            self.refresh_display()
            self.stdscr.timeout(1000)  # allows screen to refresh without requiring user input (every 1 second)
            ch = self.stdscr.getch()

            if ch == curses.KEY_RESIZE:  # resize window
                oldx = x
                oldy = y
                y, x = self.stdscr.getmaxyx()
                self.main_screen.clear()
                self.main_screen.resize(y-2, x)
                self.top_bar.clear()
                self.bottom_bar.clear()
                self.bottom_bar.mvwin(y-1, 0)
                y, x = self.main_screen.getmaxyx()
                self.stdscr.clear()
                if oldy > y:
                    test_offset = test_offset + (oldy-y)
                    self.selected -= (oldy-y)
                elif oldy < y:
                    test_offset = test_offset - (y-oldy)
                    if test_offset < 0:
                        test_offset = 0
                    else:
                        self.selected += (y-oldy)
                self.set_bars()
                self.stdscr.refresh()

            elif ch == curses.KEY_UP or ch == ord('k'):  # handle moving the cursor position
                if self.selected > 0:
                    self.selected -= 1
                else:
                    if test_offset > 0:
                        test_offset -= 1
            elif ch == curses.KEY_DOWN or ch == ord('j'):
                if self.selected < y-1:  # minus one when you factor in the bottom bar
                    self.selected += 1
                else:
                    if test_offset < len(service_list)-y:
                        test_offset += 1

            elif ch == curses.KEY_RIGHT or ch == curses.ascii.ACK:  # ctrl-f to page forwords
                test_offset += y
                if test_offset > len(service_list) - y:
                    test_offset = len(service_list) - y
            elif ch == curses.KEY_LEFT or ch == curses.ascii.STX:  # ctrk-b to page back backwords
                test_offset -= y
                if test_offset < 0:
                    test_offset = 0
            elif ch == ord("H"):
                self.selected=0
            elif ch == ord("M"):
                self.selected=int(y/2)
            elif ch == ord("L"):
                self.selected=y-1

            elif ch == ord('/'):
                self.search()

            elif ch == ord('w'): #  DEBUG
                self.top_bar.addstr(0,0,service_list[self.selected+test_offset].name,curses.A_REVERSE)

            elif ch == ord('s'):  # start service
                manager.start(service_list[self.selected+test_offset].name)
            elif ch == ord('x'):  # stop service
                manager.stop(service_list[self.selected+test_offset].name)
                continue
            elif ch == ord('r'):  # restart service
                manager.restart(service_list[self.selected+test_offset].name)
                continue
            elif ch == ord('e'):  # enable service
                manager.enable(service_list[self.selected+test_offset].name)
                continue
            elif ch == ord('d'):  # disable service
                manager.disable(service_list[self.selected+test_offset].name)
                continue
            elif ch == ord('q'):  # quit
                return
            else:
                continue


def main():
    global thread_kill, display
    print("Getting all services from systemd")
    parse_list()
    service_list.sort(key = sort_services)
    thread = threading.Thread(target=update_service)
    thread.start()
    display = Display()
    thread_kill = 1
    display.clean_up()
    thread.join()
    exit(0)


if __name__ == "__main__":
    main()
