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

def smoothen(l):
    sum = Count(0, 0)
    for i in range(len(l)):
        sum += l[i]
        l[i] = sum - l[i]
    l.append(sum)

class Count:
    def __init__(self, messages, characters):
        self.messages = messages
        self.characters = characters
    
    def __add__(self, other):
        return Count(self.messages + other.messages, self.characters + other.characters)

    def __sub__(self, other):
        return Count(self.messages - other.messages, self.characters - other.characters)

min_date = datetime.date(3000, 12, 31)
max_date = datetime.date(1000, 1, 1)

class Partner:
    def __init__(self, name):
        self.name = name
        self.sent = Count(0, 0)
        self.received = Count(0, 0)
        self.total = Count(0, 0)
        self.sent_by_date = dict()
        self.received_by_date = dict()

    def register(self, msg):
        global min_date
        global max_date
        count = Count(1, count_chars(msg))
        sender_name = fix(msg['sender_name'])
        date = datetime.date.fromtimestamp(msg['timestamp_ms'] / 1000)
        min_date = min(min_date, date)
        max_date = max(max_date, date)
        if sender_name == self.name:
            self.sent += count
            if not date in self.sent_by_date:
                self.sent_by_date[date] = count
            else:
                self.sent_by_date[date] += count
            self.total += count
        elif sender_name == my_name:
            self.received += count
            if not date in self.received_by_date:
                self.received_by_date[date] = count
            else:
                self.received_by_date[date] += count
            self.total += count
        else:
            print('Unknown sender: ' + sender_name, file=sys.stderr)
    
    def process_histories(self):
        days = date_diff(min_date, max_date) + 1
        self.sent_history = [Count(0, 0)] * days
        self.received_history = [Count(0, 0)] * days
        for date, sent in self.sent_by_date.items():
            day = date_diff(min_date, date)
            self.sent_history[day] = sent
        for date, received in self.received_by_date.items():
            day = date_diff(min_date, date)
            self.received_history[day] = received
        smoothen(self.sent_history)
        smoothen(self.received_history)
        self.total_history = [self.sent_history[i] + self.received_history[i] for i in range(days + 1)]


def extract(use_chars, x):
    if use_chars:
        return x.characters
    else:
        return x.messages

partners = []

# my_name - your name on Facebook
def load_data(my_name):
    global partners
    global min_date
    global max_date

    partners = []
    min_date = datetime.date(3000, 12, 31)
    max_date = datetime.date(1000, 1, 1)

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
            print('Broken file: ' + file, file=sys.stderr)
            continue
            
        partner_name = fix(data['participants'][0]['name'])

        partner = Partner(partner_name)

        for msg in data['messages']:
            partner.register(msg)
        
        if partner_name == my_name:
            print(partner_name + ' has the same name as you. Ignoring ' + str(partner.sent.messages) + ' messages with ' + str(partner.sent.characters) + ' characters.', file=sys.stderr)
            continue

        partners.append(partner)

    for p in partners:
        p.process_histories()

# partners - The list of partners.
# use_chars - True to count (non-whitespace) characters, False to count messages.
# start_date - The start date of the count/plot.
# count_all - True to count all characters/messages ever sent, False to only count since the start date.
def update_partners(partners, use_chars, start_date, count_all):
    start_day = max(0, date_diff(min_date, start_date)) + 1
    if count_all:
        partners.sort(key=lambda x: extract(use_chars, x.total), reverse=True)
    else:
        partners.sort(key=lambda x: extract(use_chars, x.total - x.total_history[start_day - 1]), reverse=True)

# use_chars - True to count (non-whitespace) characters, False to count messages.
# start_date - The start date of the count/plot.
# count_all - True to count all characters/messages ever sent, False to only count since the start date.
def print_partners(use_chars, start_date, count_all, to_file, file_name=''):
    start_day = max(0, date_diff(min_date, start_date)) + 1
    partners_updated = partners.copy()
    update_partners(partners_updated, use_chars, start_date, count_all)

    total_received = Count(0, 0)
    total_sent = Count(0, 0)
    for p in partners_updated:
        total_received += p.sent
        total_sent += p.received
        if not count_all:
            total_received -= p.sent_history[start_day - 1]
            total_sent -= p.received_history[start_day - 1]
    
    if to_file:
        out_file = open(file_name, "w+")

    if use_chars:
        title = 'Characters'
    else:
        title = 'Messages'
    title += ' received/sent'
    if count_all:
        title += ' in all time'
    else:
        title += ' since ' + str(start_date.year) + '-' + str(start_date.month) + '-' + str(start_date.day)
    title += ':\n'
    if to_file:
        out_file.write(title + '\n')
    else:
        print('\n' + title)

    tot_str = 'Total: ' + str(extract(use_chars, total_received)) + ' Me: ' + str(extract(use_chars, total_sent))
    if to_file:
        out_file.write(tot_str + '\n')
    else:
        print(tot_str)
    
    rank = 0
    for p in partners_updated:
        rank += 1
        if count_all:
            p_str = str(rank) + '. ' + p.name + ': ' + str(extract(use_chars, p.sent)) + ' Me: ' + str(extract(use_chars, p.received))
        else:
            p_str = str(rank) + '. ' + p.name + ': ' + str(extract(use_chars, p.sent - p.sent_history[start_day - 1])) + ' Me: ' + str(extract(use_chars, p.received - p.received_history[start_day - 1]))
        if to_file:
            out_file.write(p_str + '\n')
        else:
            print(p_str)


# use_chars - True to count (non-whitespace) characters, False to count messages.
# start_date - The start date of the count/plot.
# count_all - True to count all characters/messages ever sent, False to only count since the start date.
# shown_partners - How many people to plot (the top shown_partners by total characters/messages are plotted).
# message_direction -  sent, received, total
def plot_partners(use_chars, start_date, count_all, shown_partners, message_direction):
    assert(message_direction == 'sent' or message_direction == 'received' or message_direction == 'both')
    plt.clf()
    start_day = max(0, date_diff(min_date, start_date)) + 1
    for p in partners[:shown_partners]:
        if message_direction == 'sent':
            history = p.received_history
        elif message_direction == 'received':
            history = p.sent_history
        else:
            history = p.total_history
        if count_all:
            data = [extract(use_chars, elem) for elem in history[start_day:]]
        else:
            data = [extract(use_chars, elem - history[start_day - 1]) for elem in history[start_day:]]
        plt.plot(data, label=p.name)
    plt.legend()
    
    if use_chars:
        title = 'Characters'
    else:
        title = 'Messages'
    if message_direction == 'sent':
        title += ' sent'
    elif message_direction == 'received':
        title += ' received'
    else:
        title += ' exchanged'
    if count_all:
        title += ' in all time'
    else:
        title += ' since ' + str(start_date.year) + '-' + str(start_date.month) + '-' + str(start_date.day)
    plt.title(title)

    if use_chars:
        plt.ylabel('Characters')
    else:
        plt.ylabel('Messages')
    plt.xlabel('Date')
    end_day = date_diff(min_date, max_date) + 2
    all_dates = [min_date + datetime.timedelta(days = x - 1) for x in range(start_day, end_day)]
    dates = [date for date in all_dates if date.day == 1 and (date.month - 1) % 3 == 0]
    date_names = [month_names[date.month - 1] + ' ' + str(date.year) for date in dates]
    days = [date_diff(min_date, date) + 1 - start_day for date in dates]
    plt.xticks(days, date_names, rotation=35)
    plt.draw()

# Arguments: 
my_name = ''
use_chars = True
start_date = datetime.date(2013, 1, 1)
count_all = False
shown_partners = 15
message_direction = 'both'

def press(event):
    global partners
    global use_chars
    global start_date
    global count_all
    global shown_partners
    global message_direction
    change = True
    if event.key == 'c' and use_chars == False:
        use_chars = True
    elif event.key == 'm' and use_chars == True:
        use_chars = False
    elif event.key == 'd':
        y = int(input('Start date year: '))
        m = int(input('Start date month: '))
        d = int(input('Start date day: '))
        start_date = datetime.date(y, m, d)
    elif event.key == 'z' and count_all == True:
        count_all = False
    elif event.key == 'a' and count_all == False:
        count_all = True
    elif event.key == 'n':
        shown_partners = int(input('Number of partners to plot: '))
        shown_partners = max(1, shown_partners)
        shown_partners = min(len(partners), shown_partners)
    elif event.key == '+' and shown_partners < len(partners):
        shown_partners += 1
        shown_partners = min(len(partners), shown_partners)
    elif event.key == '-' and shown_partners > 1:
        shown_partners -= 1
        shown_partners = max(1, shown_partners)
    elif event.key == 't' and message_direction != 'sent':
        message_direction = 'sent'
    elif event.key == 'r' and message_direction != 'received':
        message_direction = 'received'
    elif event.key == 'b' and message_direction != 'both':
        message_direction = 'both'
    elif event.key == 'u':
        update_partners(partners, use_chars, start_date, count_all)
    else:
        change = False
        if event.key == 'p':
            print_partners(use_chars, start_date, count_all, False)
        elif event.key == 'w':
            file_name = input('File name: ')
            print_partners(use_chars, start_date, count_all, True, file_name)
    if change:
        plot_partners(use_chars, start_date, count_all, shown_partners, message_direction)

my_name = input('Enter your name on Facebook: ')
load_data(my_name)

fig, ax = plt.subplots()
fig.canvas.mpl_connect('key_press_event', press)

print()
print('Help guide:')
print('C - count (non-whitespace) characters')
print('M - count messages')
print('D - change the start date')
print('Z - only count messages since the start date')
print('A - count all messages')
print('N - change the number of chats to plot (top X chats sorted by messages/characters are shown)')
print('+ - increment the above number by one')
print('- - decrement the above number by one')
print('T - only count messages sent by you')
print('R - only count messages sent by the other person')
print('B - count both')
print('U - update the ranking (sort by bidirectional messages/characters since the start date, if applicable)')
print('P - print total stats per person (optionally since the start date only)')
print('W - write total stats per person to a file (optionally since the start date only)')

update_partners(partners, use_chars, start_date, count_all)
plot_partners(use_chars, start_date, count_all, shown_partners, message_direction)

plt.show()
