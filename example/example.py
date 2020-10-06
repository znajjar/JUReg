from jureg import JUReg


def target_function(courses):
    for course in courses:
        out = '{} section(s) from {} are open:'.format(str(len(courses[course])), course)
        for sec in range(len(courses[course])):
            out += ' {}'.format(courses[course][sec])
            if sec != len(courses[course]) - 1:
                out += ','
        print(out)
    pass


ju = JUReg(filepath='login.txt', target=target_function)
ju.add_sections('0907528', [1, 2, 3])
ju.run()
