from jureg import JUReg
from win10toast import ToastNotifier


def target_function(courses):
    if not len(courses): return
    notifications = ''
    for course in courses:
        noti = course + ':'
        for sec in range(len(courses[course])):
            noti += ' {}'.format(courses[course][sec])
            if sec != len(courses[course]) - 1:
                noti += ','
        notifications += noti + '\n'
        print(noti)
    toaster.show_toast('Open Sections Found', notifications, duration=30)


toaster = ToastNotifier()
username = input('username: ')
password = input('password: ')
ju = JUReg(username=username, password=password, target=target_function, driver='ch', refresh=1)
ju.add_sections('0301211', [1, 2])
ju.add_sections('0907528', [1, 2, 3])
ju.run()
print('running..')
