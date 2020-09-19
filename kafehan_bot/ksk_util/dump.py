from datetime import datetime
from pprint import pprint


def new_dump_txt(obj):
    with open('dump.txt', 'w') as f:
        f.write('\n\n\n' + str(datetime.now()) + '\n')
        pprint(obj, stream=f)


def add_dump_txt(obj):
    with open('dump.txt', 'a') as f:
        f.write('\n\n\n' + str(datetime.now()) + '\n')
        pprint(obj, stream=f)
