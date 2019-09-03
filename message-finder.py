from __future__ import print_function
import os
import json
import datetime
import sys
import matplotlib.pyplot as plt

chat_root = 'messages/inbox'
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def fix(s):
    return s.encode('latin1').decode('utf8')

def count_chars(msg):
    try:
        content = fix(msg['content'])
        no_whites = ''.join(content.split())
        return len(no_whites)
    except KeyError:
        return 0

def date_diff(f, t):
    return (t - f).days

# my_name - your name on Facebook
def load_data(my_name):

    for f in os.listdir(chat_root):
        file = os.path.join(chat_root, f, 'message_1.json')
        try:
            data = json.load(open(file, 'r'))
        except FileNotFoundError:
            continue

        if data['thread_type'] != 'Regular':
            continue

        try:
            assert(len(data['participants']) == 2 and fix(data['participants'][1]['name']) == my_name)
        except AssertionError:
            continue

        partner_name = fix(data['participants'][0]['name'])

        if partner_name != target_name:
            continue

        for msg in reversed(data['messages']):
            date = datetime.date.fromtimestamp(msg['timestamp_ms'] / 1000)
            dtime = datetime.datetime.fromtimestamp(msg['timestamp_ms'] / 1000)
            if start_date <= date and date <= end_date:
                sender_name = fix(msg['sender_name'])
                try:
                    text = fix(msg['content'])
                except KeyError:
                    text = 'Sticker, file, etc.'
                print(str(date.day) + '-' + month_names[date.month-1] + '-' + str(date.year) + ' ' + str(dtime.hour) + ':' + str(dtime.minute) + ':' + str(dtime.second))
                print(sender_name + ': ' + text)

# Arguments: 
my_name = ''
target_name = ''
start_date = datetime.date(2018, 4, 4)
end_date = datetime.date(2018, 4, 4)

# my_name = input('Enter your name on Facebook: ')
load_data(my_name)
