#!/use/bin/python
import re
import praw
from prawcore import PrawcoreException
import time
from datetime import timedelta, date, datetime
import datetime as dt
import os
from prawcore.exceptions import NotFound
import traceback

BanLength = 31
HistoryBackdateDays = 30

reddit = praw.Reddit('GOGThreadChecker', user_agent='GOGThreadChecker')

print("Starting GOG Thread Checker bot...")

while True:
    try:
        
##        with open("GamesAMonth.txt", 'r') as GamesAMonthRead:
##            for line in GamesAMonthRead:
                
        if not os.path.isfile("GOGThreadLog.txt"):
            GOGThreadLog = []
        else:
            with open("GOGThreadLog.txt", "r") as f:
                GOGThreadLog = f.read()
                GOGThreadLog = GOGThreadLog.split("\n")
                GOGThreadLog = list(filter(None, GOGThreadLog))

        Wiki = reddit.subreddit('GiftofGames').wiki['giftlog']
        for line in Wiki.content_md.splitlines():
            line = line.strip()
            GOGLine = re.search('(?i)(\S*?) gifted (\S*?) (.*?) for (.*?) on (\d\d/\d\d/\d\d\d\d)$', line)
            if GOGLine is not None and "beta" not in GOGLine.group(3).lower() and str(GOGLine) not in GOGThreadLog:
##                    print("Reading new line")
                Gifter = GOGLine.group(1)
                if "ourrobotoverlord" in str(Gifter).lower():
                    Gifter = ""
                GifterNoSpecial = Gifter.replace("-", "").replace("_", "")
                GifterSpaceSpecial = Gifter.replace("-", " ").replace("_", " ")
                Giftee = GOGLine.group(2)
                Gift = GOGLine.group(3)
                Platform = GOGLine.group(4)

                GiftDate = datetime.strptime(GOGLine.group(5), '%d/%m/%Y')
                GiftDateBacklog = GiftDate + timedelta(HistoryBackdateDays)
                Today = datetime.today()
                if Today > GiftDateBacklog:
##                        print(Gift, "from", Gifter, "to", Giftee, "too old to enforce. Skipping.")
                    continue

##                    print("Checking", Giftee, "for", Gift, "from", Gifter)                    
                try:
##                        print("Checking server ban list")
                    if any(reddit.subreddit("GiftofGames").banned(redditor=Giftee)):
##                            print(Giftee, "is banned.")
                        continue
                    else:
##                            print(Giftee, "not banned; proceeding.")
                        GOGFound = False
                        try:
                            ##Below returns top 500 posts from receiver
                            UserPosts = reddit.redditor("{}".format(Giftee)).submissions.new(limit=500)
                            for post in UserPosts:
##                                    print(post.title)
                                if post is not None:
##                                        print(post.title)
                                    try:
                                        GOGThread = re.search(rf'(?i)\[GOG\].*({Gifter}|{GifterNoSpecial}|{GifterSpaceSpecial})', post.title)
                                        if GOGThread is not None:
##                                                print(str(post.title), Giftee, Gifter)
                                            GOGFound = True
                                            break
                                    except Exception as e:
                                        print(e)

                            if GOGFound is True:
##                                  print("[GOG] post by", Giftee, "for", Gifter, "found.")
                                GOGThreadLog.append(GOGLine)
                                with open("GOGThreadLog.txt", "a+") as GOGThreadLogOpen:
                                    GOGThreadLogOpen.write(str(GOGLine) + "\n")
                                    GOGThreadLogOpen.close()
                                continue
                            
                            else:
                                ThreeDaysAfter = GiftDate + timedelta(days=3)
##                                    print(Giftee, Today, ThreeDaysAfter)
                                GOGLineReminded = str((str(GOGLine).replace("(", "\(").replace(")", "\)").replace("^", "\^").replace("$", "\$").replace("-", "\-").replace("+", "\+").replace("*", "\*").replace("?", "\?").replace("[", "\[").replace("]", "\]").replace("{", "\{").replace("}", "\}").replace("|", "\|").replace("!", "\!") + " REMINDED"))
##                                    print(GOGLineReminded)
                                if GOGLine not in GOGThreadLog:
                                    RemindDateSearch = re.search(fr"(?i){GOGLineReminded} (\d\d\d\d-\d\d-\d\d).*?\n", open('GOGThreadLog.txt', 'r').read())
                                    if RemindDateSearch is not None:
                                        RemindDate = datetime.strptime(RemindDateSearch.group(1), '%Y-%m-%d')
                                        SevenDaysAfter = RemindDate + timedelta(days=4)
                                        if Today > SevenDaysAfter:
                                            print("No GOG thread for", Gifter, "by", Giftee, "found after reminding. Banning.")
                                            reddit.subreddit("GiftofGames").banned.add(Giftee, ban_reason='No GOG thread', duration=BanLength, ban_message='**Reason:** No [GOG] thread post found to thank {} for {}. \n\nPlease read the [full rules](https://www.reddit.com/r/GiftofGames/wiki/rules) \n\nThis action was performed by a bot. Please reply to this message if you believe this action was made in error'.format(Gifter,Gift))
                                            GOGThreadLog.append(GOGLine)
                                            with open("GOGThreadLog.txt", "a+") as GOGThreadLogOpen:
                                                GOGThreadLogOpen.write(str(GOGLine) + "\n")
                                                GOGThreadLogOpen.close()
                                            continue
                                        else:
##                                                print(Giftee, "reminded but allowing time to post.")
                                            continue
                                            
                                    elif Today > ThreeDaysAfter:
                                        try:
                                            print("No GOG thread for", Gifter, "by", Giftee, "found. Sending reminder.")
                                            reddit.subreddit("GiftofGames").modmail.create("Reminder to post [GOG] thread", "As a reminder, all gifts received on this subreddit require you to post a [GOG] thank you thread ***with the gifter's username in the title***. \n\nNo [GOG] thank you thread to {} for {} found. Failure to post one will result in a ban. \n\nNo response to this message is needed unless you believe it was made in error.".format(Gifter,Gift), "{}".format(Giftee))
                                            GOGLineRemindedRaw = str(GOGLine) + " REMINDED " + str(Today)
                                            GOGThreadLog.append(GOGLineRemindedRaw)
                                            with open("GOGThreadLog.txt", "a+") as GOGThreadLogOpen:
                                                GOGThreadLogOpen.write(GOGLineRemindedRaw + "\n")
                                                GOGThreadLogOpen.close()
                                        except Exception as e:
                                            print(e)
                                        continue

                                    else:
##                                            print("Giving", Giftee, "until", ThreeDaysAfter, "before reminding.")
                                        continue
                            
                        except PrawcoreException as e:
                            if "404" in str(e):
                                print(Giftee, "deleted their account. Skipping future checks.")
                                GOGThreadLog.append(GOGLine)
                                with open("GOGThreadLog.txt", "a+") as GOGThreadLogOpen:
                                    GOGThreadLogOpen.write(str(GOGLine) + "\n")
                                    GOGThreadLogOpen.close()
                            elif "403" in str(e):
                                print(e, Giftee)
                            else:
                                print(e, Giftee)
                        
                except Exception as e:
                    if "500" in str(e):
                        print(Giftee, "has no posts. Skipping future checks.")
                        GOGThreadLog.append(GOGLine)
                        with open("GOGThreadLog.txt", "a+") as GOGThreadLogOpen:
                            GOGThreadLogOpen.write(str(GOGLine) + "\n")
                            GOGThreadLogOpen.close()
                    continue
                    
    except Exception as e:
        print(e, Giftee, traceback.format_exc())
