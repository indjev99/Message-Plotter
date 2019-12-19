from __future__ import print_function
import os
import json
import datetime
import sys
import matplotlib.pyplot as plt

chat_root = os.path.join('messages', 'inbox')
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

def format(n):
    return '{:02d}'.format(n)

# my_name - your name on Facebook
def print_messages(my_name, target_name, start_date, end_date):
    for f in os.listdir(chat_root):
        all_messages = []
        for num in range(1000):
            msg_name = 'message_' + str(num + 1) + '.json'
            file = os.path.join(chat_root, f, msg_name)
            try:
                data = json.load(open(file, 'r'))
            except FileNotFoundError:
                break

            if num == 0:
                if data['thread_type'] != 'Regular':
                    break
                try:
                    assert(len(data['participants']) == 2 and fix(data['participants'][1]['name']) == my_name)
                except AssertionError:
                    break
                partner_name = fix(data['participants'][0]['name'])
                if partner_name == my_name:
                    break
                if partner_name != target_name:
                    break

            all_messages += data['messages']

        for msg in reversed(all_messages):
            date = datetime.date.fromtimestamp(msg['timestamp_ms'] / 1000)
            dtime = datetime.datetime.fromtimestamp(msg['timestamp_ms'] / 1000)
            if start_date <= date and date <= end_date:
                sender_name = fix(msg['sender_name'])
                try:
                    text = fix(msg['content'])
                except KeyError:
                    text = 'Sticker, file, etc.'
                print(format(date.day) + '-' + month_names[date.month-1] + '-' + str(date.year) + ' ' + format(dtime.hour) + ':' + format(dtime.minute) + ':' + format(dtime.second))
                print(sender_name + ': ' + text)

# Arguments:
my_name = ''
target_name = ''
start_date = datetime.date(2018, 4, 4)
end_date = datetime.date(2018, 4, 4)

if __name__ == '__main__':
    print_messages(my_name, target_name, start_date, end_date)
