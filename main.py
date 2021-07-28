import os
import requests
import time
import datetime as dt
import schedule
import pandas as pd
import pytz
from telegram.ext import *
import threading
import logging
import json
IST = pytz.timezone('Asia/Kolkata')

# Secrets for the program
my_secret = os.environ['API'].strip()
groupid = os.environ['__groupid__'].strip()
googleSheetId_attendance = os.environ['Attendance'].strip()
googleSheetId_images = os.environ['Images'].strip()
googleSheetId_holiday = os.environ['Holiday'].strip()
api_url_telegram = "https://api.telegram.org/bot"+my_secret+"/sendMessage?chat_id="+groupid+"&text="
api_url_attendance_telegram = "https://api.telegram.org/bot"+my_secret+"/sendMessage"

# Timetable fetching and scheduling function
def time_table():
    global IST, googleSheetId_attendance
    schedule.clear('attendance')
    now = dt.datetime.now(IST)
    now_day = now.strftime("%A").upper()
    worksheetName = 'time_table'
    URL = 'https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}'.format(googleSheetId_attendance, worksheetName)
    data_list = pd.read_csv(URL)
    new_sorted_data = data_list[['SLOT', now_day]]
    data = list(new_sorted_data.to_dict(orient="records"))
    for each_slot in data:
        if str(each_slot[now_day]) != 'nan':
            time_ = each_slot[now_day].split("/")[1].strip()
            correct_time = str((dt.datetime.strptime(time_, "%H:%M") - dt.datetime.strptime('05:30', "%H:%M")))
            # For correcting UTC at 00:00 otherwise -1day,18:30
            if len(correct_time.split(',')) != 2:
                day_ = now_day
                hr = f'{int(correct_time.split(":")[0]):02d}'
                time_ = f'{hr}:{correct_time.split(":")[1]}'
            else:
                day_ = (now-dt.timedelta(days=1)).strftime('%A')
                hr = f'{int(correct_time.split(",")[1].split(":")[0]):02d}'
                time_ = f'{hr}:{correct_time.split(",")[1].split(":")[1]}'

            if len(each_slot[now_day].split("/")) == 2:
                exec(f'schedule.every().{day_.lower()}.at("{time_}").do(lambda: attendance("{each_slot[now_day].split("/")[0].strip()}","")).tag("attendance")')
            else:
                exec(f'schedule.every().{day_.lower()}.at("{time_}").do(lambda: attendance("{each_slot[now_day].split("/")[0].strip()}","{"/".join(each_slot[now_day].split("/")[2:]).strip()}")).tag("attendance")')
                

# Updating timetable and checking before each session
def schedule_timetable():
    schedule.every().day.at("02:29").do(time_table).tag("timetable")
    schedule.every().day.at("03:29").do(time_table).tag("timetable")
    schedule.every().day.at("04:44").do(time_table).tag("timetable")
    schedule.every().day.at("05:44").do(time_table).tag("timetable")
    schedule.every().day.at("07:29").do(time_table).tag("timetable")
    schedule.every().day.at("08:29").do(time_table).tag("timetable")
    schedule.every().day.at("09:29").do(time_table).tag("timetable")
    schedule.every().day.at("10:29").do(time_table).tag("timetable")
    schedule.every().day.at("11:29").do(time_table).tag("timetable")


def start_all():
    global Cancel_Attendance_Remainder_Status
    Cancel_Attendance_Remainder_Status = False
    # schedule for if_holiday function
    schedule.clear('if_holiday')
    schedule.every().day.at("18:30").do(if_holiday).tag("if_holiday")
    if_holiday()


def stop_all():
    global Cancel_Attendance_Remainder_Status
    Cancel_Attendance_Remainder_Status = False
    cancel_all()
    schedule.clear('if_holiday')
    schedule.clear('goodmorning')


def cancel_all():
    global Cancel_Attendance_Remainder_Status
    Cancel_Attendance_Remainder_Status = True
    schedule.clear('attendance')
    schedule.clear('timetable')


def schedule_all():
    global Cancel_Attendance_Remainder_Status
    Cancel_Attendance_Remainder_Status = False
    schedule.clear('attendance')
    schedule.clear('timetable')
    time_table()
    schedule_timetable()    


# Function to sent any message
def send_message_telegram(message):
    final_telegram_url = api_url_telegram + message
    requests.get(final_telegram_url) 


# Function to greet goodmorning with random images from google drive    
def good_morning():
    global googleSheetId_images
    with open("no.txt", "r") as file:
        data = file.readlines()
        no = data[0]
    worksheetName = 'images_url'
    URL = "https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}".format(googleSheetId_images, worksheetName)
    data_list = list(pd.read_csv(URL)["FILE ID"])

    if no == "100":
        with open("no.txt", "w") as f:
            f.write("0")
    
    file_id = data_list[int(no)].split('/')[5]
    
    with open("no.txt", "w") as f:
        new_num = int(no) + 1
        f.write(str(new_num))    

    url = 'https://drive.google.com/uc?id='+file_id
    page = requests.get(url)
    file = open("sample_image.png", "wb")
    file.write(page.content)
    file.close()
    files = {
      'photo': open("sample_image.png", "rb")
    }
    requests.get(f"https://api.telegram.org/bot"+my_secret+"/sendPhoto?chat_id="+groupid+"&caption=Good Morning!", files=files)
    os.remove("sample_image.png")


# Default value
if_today_is_holiday = False
Cancel_Attendance_Remainder_Status = False


# checking for whether today is holiday from google sheet
def if_holiday():
    global if_today_is_holiday, Cancel_Attendance_Remainder_Status
    # Resetting history
    if_today_is_holiday = False
    schedule.clear('goodmorning')
    schedule.clear('attendance')
    schedule.clear('timetable')
    now = dt.datetime.now(IST)
    now_day = now.strftime("%d/%m/%y")
    worksheet = 'holiday'
    URL_holiday = 'https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}'.format(googleSheetId_holiday, worksheet)
    holiday_dates_list = pd.read_csv(URL_holiday)
    dates = list(holiday_dates_list["HOLIDAY"])
    if now_day in dates:
        if_today_is_holiday = True

    if if_today_is_holiday:
        cancel_all()

        if now.strftime("%H:%M") == '00:00':
            data_dict = list(holiday_dates_list.to_dict(orient="records"))[dates.index(now_day)]
            file_id_holiday = data_dict['FILEID']
            caption = data_dict['CAPTION']
            if str(file_id_holiday) != 'nan':
                if str(caption) == 'nan':
                    caption = ''
                url = 'https://drive.google.com/uc?id=' + file_id_holiday.split('/')[5]
                page = requests.get(url)
                file = open("sample_image.png", "wb")
                file.write(page.content)
                file.close()
                files = {
                    'photo': open("sample_image.png", "rb")
                }
                requests.get(
                    f"https://api.telegram.org/bot" + my_secret + "/sendPhoto?chat_id=" + groupid + f"&caption={caption}",
                    files=files)
                os.remove("sample_image.png")

    else:
        # schedule for goodmorning function
        schedule.every().day.at("00:30").do(good_morning).tag("goodmorning")
        if not Cancel_Attendance_Remainder_Status:
            time_table()
            schedule_timetable()


# Function to pass attendance message
def attendance(sub, url_):
    if url_ != '':
        pass
    else:
        url_ = 'https://eduserver.nitc.ac.in/'
    
    params = {
        'chat_id': '-1001576827434',
        'parse_mode': 'HTML',
        'text': f'Guys Mark attendance for <b>{sub}</b>\n👇',
        'reply_markup': json.dumps({'inline_keyboard': [[{'url': url_, 'text': 'Click Here For The Link!'}]]}, separators=(',', ':'))
    } 
    requests.get(api_url_attendance_telegram, params=params)


# For starting functions at the time of Deploying
start_all()

# Bot to receive commands
# Set up the logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.info('Starting Bot...')


def reset_attendance_reminder(bot, context):
    global if_today_is_holiday, Cancel_Attendance_Remainder_Status
    if if_today_is_holiday:
        bot.message.reply_text(f'✨  Hello,  {(bot.message.from_user.first_name)}\nSorry, Cannot Reset as today is Holiday ❌')
    elif Cancel_Attendance_Remainder_Status:
        bot.message.reply_text(f'✨  Hello,  {(bot.message.from_user.first_name)}\nSorry, Cannot Reset as Cancel all function is Activated ❌')
    else:
        time_table()
        bot.message.reply_text(f'✨  Hello,  {(bot.message.from_user.first_name)}\nAttendance Reminder Schedule Reset Successfully ✅')


def startall(bot, context):
    start_all()
    bot.message.reply_text(f'💫  Hello,  {(bot.message.from_user.first_name)}\nProgram all started Successfully 👍')


def stopall(bot, context):
    stop_all()
    bot.message.reply_text(f'💫  Hello,  {(bot.message.from_user.first_name)}\nProgram all stopped Successfully 👍')


def resetall(bot, context):
    if Cancel_Attendance_Remainder_Status:
        bot.message.reply_text(f'✨  Hello,  {(bot.message.from_user.first_name)}\nSorry, Cannot Reset as Cancel all function is Activated ❌')
    else:
        if_holiday()
        bot.message.reply_text(f'💫  Hello,  {(bot.message.from_user.first_name)}\nReset\n1. Holiday status Successfully 👍\n2. Attendance Reminder Schedule Successfully 👍\n3. Scheduled Timetable Alternative check Successfully 👍')


def cancelall(bot, context):
    cancel_all()
    bot.message.reply_text(f'💫  Hello,  {(bot.message.from_user.first_name)}\nCancelled\n1. Attendance Reminder Successfully 👍\n2. Timetable Alternative check Successfully 👍')


def scheduleall(bot, context):
    global if_today_is_holiday
    if if_today_is_holiday:
        bot.message.reply_text(f'✨  Hello,  {(bot.message.from_user.first_name)}\nSorry, Cannot Schedule all as today is Holiday ❌')
    else:
        schedule_all()
        bot.message.reply_text(f'🌟  Hello,  {(bot.message.from_user.first_name)}\nScheduled\n1. Attendance Reminder Successfully 👍\n2. Timetable Alternative check Successfully 👍')


def error(update, context):
    # Logs errors
    logging.error(f'Update {update} caused error {context.error}')


def boot():
    updater = Updater(my_secret, use_context=True)
    dp = updater.dispatcher

    # Commands
    dp.add_handler(CommandHandler('resetattendance9329', reset_attendance_reminder))
    dp.add_handler(CommandHandler('start9329', startall))
    dp.add_handler(CommandHandler('stop9329', stopall))
    dp.add_handler(CommandHandler('resetall9329', resetall))
    dp.add_handler(CommandHandler('cancelall9329', cancelall))
    dp.add_handler(CommandHandler('scheduleall9329', scheduleall))

    # Log all errors
    dp.add_error_handler(error)

    # Run the bot
    updater.start_polling(1.0)
    # updater.idle()


# Loop to check the pending schedule
def loop_():
    while True:
        schedule.run_pending()
        time.sleep(1)
  

if __name__ == "__main__":
    # creating thread
    t1 = threading.Thread(target=loop_)
    t2 = threading.Thread(target=boot)
    # starting thread 1
    t1.start()
    # starting thread 2
    t2.start()
    # wait until thread 1 is completely executed
    t1.join()
    # wait until thread 2 is completely executed
    t2.join()