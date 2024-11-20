#!/usr/bin/python3

"""
Libraries:

urllib: Used for scanning and reading HTML pages from TARGET Servers
re: Regex library used for searching for data in a particular format. Namely searching HTML pages for <team> tags
configparser Parser library used for parsing scores and configuration data.
time: Time used for delaying score updates at a set interval.
os: Currently only used for removing uneeded template files generated on initialization.
    Used to make general OS calls as needed.
csv: used for parsing comma delimited lists for the White and Black Lists.
imp: used for importing plugins (Propane Accessories).
datetime: used for scheduling games using a start/end time.
thread (Timer): The Timer is used to spawn a thread that will end the game 
                once deltaTime value generated from the endtime in the config reaches 0.
socket: Used to determine connections to a server/service.
shutil (copyfile, copytree): Used to copy files where ever they are needed. Used specifically for the scoreboard backups, template loading, and copying relevant configs.

"""
import urllib.request
import re
import configparser
import time
import os
import csv
#import imp
from datetime import datetime
from threading import Timer
import socket
from shutil import copyfile, copytree
import psycopg2
from psycopg2 import Error


# Colors for terminal output. Makes things pretty.
class bcolors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[31m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    BGRED = '\033[41m'
    WHITE = '\033[37m'
    CYAN = '\033[36m'

'''
Globals:

config: Initialize the parser that will be used to parse the propane_config file.
scores: Initialize the parser that will be used to parse the propane_scores file.
configFile: Initialize global string where the path to the propane_config will be stored.
serversToCheck: Initialize global where the parsed data about the Servers from the propane_config will be stored.
                (Initialized as string, but will be used as a list)
whiteListInit: Initialize the white list global value that will be used to store the users option from the WhiteList section.
blackListInit: Initialize the black list global value that will be used to store the users option from the BlackList section.
sleeptTime: Initialize global that will store the delay interval that is parsed from propane_config.
            (Initialized as string, but will be used as a number)
outfile: Initialize global string that will store the desired location and name of the main scoreboard output file.
         (usually /var/www/html/index.html or /var/www/index.html in Apache)
outdir: Initialize the global string that will store the desired output location of the template.
        This is usally the same directory as outfile, but without the outfile name (e.g. /var/www/).
starttime: Initialize the global string that determines the start delay time for the main loop.
endtime: Initialize the global string that determines the end delay time for the entire program.
gameSetup: Initialize the global boolean that is used to test if this is the initial start up.
            This is used so that any set up is done only on the first iteration, but currently is
            only needed to load in the initial template.
PropAccDir: Initialize the main directory for plugins (Propane Accessories)
PropAccModule: Initialize the main module name for all plugins (Propane Accessories)
portsToCheck: Initializes the global where the parsed data about specific Ports to be checked for webservers will be stored.
                (Initialized as string, bbut will be used as a list)
'''
config = configparser.RawConfigParser()
scores = configparser.RawConfigParser()
configFile = ""
serversToCheck = []
scoresToAdd = []
whiteListInit = ""
blackListInit = ""
sleepTime = ""
outfile = ""
outfile2 = ""
outdir = ""
startTime = ""
endTime = ""
gameSetup = True
PropAccDir = "./PropAcc"
PropAccModule = "__init__"
portsToCheck = ""

'''
loadConfig():
    Loads and parses the propane_config file.
    Loads the globals "configFile, serversToCheck, whiteListInit, blackListInit, sleepTime, outfile, outdir, startTime, endTime, whiteListIsOn, blackListIsOn, enablePropAcc, showTargetIP, enableCustomPorts, portsToCheck, enableBackUp" 
    from the config file to use later on.
'''


def loadConfig():


        # Little hacky workaround for docker config sharing, don't touch if not running in docker. The official docker container handles this for you!
        isDocker = False

        if isDocker:
            if os.path.exists("/tmp/propane_config.ini"):
                print(bcolors.CYAN + bcolors.BOLD + "Copying config for docker from /tmp..." + bcolors.ENDC)
                copyfile("/tmp/propane_config.ini", "/var/www/propane_config.ini")
            else:
                print(bcolors.CYAN + bcolors.BOLD + "No config file exists yet in /tmp for docker, skipping..." + bcolors.ENDC)

        print(bcolors.CYAN + bcolors.BOLD + "Loading Configurations" + bcolors.ENDC)
        
        global configFile, serversToCheck,scoresToAdd, whiteListInit, blackListInit, sleepTime, outfile, outfile2, outdir, startTime, endTime, whiteListIsOn, blackListIsOn, enablePropAcc, showTargetIP, enableCustomPorts, portsToCheck, enableBackUp, PostgresEnabled, PostgresAddress, PostgresPort, PostgresLogin, PostgresPass, PostgresScore
        
        # Clear the config before we reload it so we don't get list memory conflict hell
        config.clear()

        configFile = config.read("propane_config.ini")
        serversToCheck = config.items("Targets")
        scoresToAdd = config.items("ScoresToAdd")
        whiteListInit = config.items("WhiteList")
        blackListInit = config.items("BlackList")
        sleepTime = config.getint("General", "sleeptime")
        outfile = config.get("General", "outfile")
        outfile2 = config.get("General", "outfile2")
        outdir = config.get("General", "outdir")
        enableBackUp = config.getboolean("General", "enableBackUp")
        startTime = config.get("General", "starttime")
        endTime = config.get("General", "endtime")
        whiteListIsOn = config.getboolean("General", "whiteListOn")
        blackListIsOn = config.getboolean("General", "blackListOn")
        enablePropAcc = config.getboolean("General", "enablePropAcc")
        showTargetIP = config.getboolean("General", "showTargetIP")
        enableCustomPorts = config.getboolean("General", "enableCustomPorts")
        portsToCheck = config.items("PortConfig")
        PostgresEnabled = config.get("PostgresConf", "PostgresEnabled")
        PostgresAddress = config.get("PostgresConf", "PostgresAddress")
        PostgresPort = config.get("PostgresConf", "PostgresPort")
        PostgresLogin = config.get("PostgresConf", "PostgresLogin")
        PostgresPass = config.get("PostgresConf", "PostgresPass")
        PostgresScore = config.get("PostgresConf", "PostgresScore")

def CheckPostgres(PostgresEnabled, PostgresAddress, PostgresPort, PostgresLogin, PostgresPass, PostgresScore, whiteList, blackList):
    if PostgresEnabled == "True":
        try:
            # Устанавливаем соединение
            connection = psycopg2.connect(
                host=PostgresAddress,
                port=PostgresPort,
                database="postgres",
                user=PostgresLogin,
                password=PostgresPass
            )
            # Создаем курсор
            cursor = connection.cursor()

            # Выполняем запрос
            query = "SELECT apt FROM apts"
            cursor.execute(query)

            # Получаем результаты
            apt_values = [row[0] for row in cursor.fetchall()]
            #print(type(apt_values))
            apt_values = list(set(apt_values)) # Оставляем только уникальные команды
            for teams in apt_values:
                teams = teams.replace("_", " ").title().replace(" ", "_")
                if whiteListIsOn and not blackListIsOn:
                    if teams in whiteList:
                        if not scores.has_option("TotalScores", teams):
                            scores.set("TotalScores", teams, 0)
                        currentScore = scores.getint("TotalScores", teams)
                        scores.set("TotalScores", teams, currentScore + int(PostgresScore))
                    else:
                        print(bcolors.FAIL + bcolors.BOLD + "Команда: " + teams + " не в вайтлисте." + bcolors.ENDC)
                elif blackListIsOn and not whiteListIsOn:
                    if teams in blackList:
                        print(bcolors.FAIL + bcolors.BOLD + "Команда: " + teams + " в блэклисте." + bcolors.ENDC)
                    else:
                        if not scores.has_option("TotalScores", teams):
                            scores.set("TotalScores", teams, 0)
                        currentScore = scores.getint("TotalScores", teams)
                        scores.set("TotalScores", teams, currentScore + int(PostgresScore))
                elif whiteListIsOn and blackListIsOn:
                    if teams in blackList:
                        print(bcolors.FAIL + bcolors.BOLD + "Команда: " + teams + " в блэклисте." + bcolors.ENDC)
                    elif teams in whiteList:
                        if not scores.has_option("TotalScores", teams):
                            scores.set("TotalScores", teams, 0)
                        currentScore = scores.getint("TotalScores", teams)
                        scores.set("TotalScores", teams, currentScore + int(PostgresScore))
                    else:
                        print(bcolors.FAIL + bcolors.BOLD + "Команда: " + teams + " не в вайтлисте." + bcolors.ENDC)
                else:
                    if not scores.has_option("TotalScores", teams):
                        scores.set("TotalScores", teams, 0)
                    currentScore = scores.getint("TotalScores", teams)
                    scores.set("TotalScores", teams, currentScore + int(PostgresScore))
        except (Exception, Error) as error:
            print(f"Ошибка при выполнении запроса: {error}")
            return None

        finally:
            # Закрываем курсор и соединение
            if cursor:
                cursor.close()
            if connection:
                connection.close()

'''
loadPropAcc():
    Imports all modules in the PropAcc Directory and returns a list of them to be initialized

'''
def loadPropAcc():

    propaccs = []
    possibleplugins = os.listdir(PropAccDir)
    for i in possibleplugins:
        location = os.path.join(PropAccDir, i)
        if not os.path.isdir(location) or not PropAccModule + ".py" in os.listdir(location):
            continue
        info = imp.find_module(PropAccModule, [location])
        propaccs.append({"name": i, "info": info})
    return propaccs


'''
initPropAcc():
    Accepts a Propane Accessory generated by the loadPropAcc function, and returns an initiliazed module
    that is imported and ready to be used.

'''
def initPropAcc(propacc):
    return imp.load_module(PropAccModule, *propacc["info"])


'''
createBackUp():
    Initializes a timestamp for the file name at the current time of backing up. Then creates a folder called "Scoreboard_Backups"
    if it does not exists already. Once the folder is made it copies the propane_scores.txt file to the backup folder with a name that is the current 
    timestamp down to the second.
'''

def createBackUp():
    currentTime = datetime.now()
    print(bcolors.CYAN + bcolors.BOLD + "Backing up scoreboard @ " + currentTime.strftime('%m-%d-%Y-%H-%M-%S') + bcolors.ENDC)
    os.makedirs("Scoreboard_Backups", exist_ok=True)
    copyfile("propane_scores.txt", "Scoreboard_Backups/" + currentTime.strftime('%m-%d-%Y-%H-%M-%S'))

'''
score():
    Loads and parses the propane_scores file.
    Iterates through the servers testing for a connection.
    If a connection is found the team tag is parsed and the appropriate team (first tag found) is awarded a point/added
    to the scoreboard.
    Writes the new score data to the propane_scores file.
    If server is not found, an error message displays in console.
    If no one owns the box scanned, then no points are awarded.
    If black list feature is on, then users in the black list are flagged in the output and no score is awarded.
    If white list is feature is on, then users not in the white list are flagged in the output and no score is awarded.
    If the back up feature is on, then the scoreboard will make a backup of itself at each scoring interval
'''

def score(whiteList, blackList):
        #Prepare for socket connection testing if webpage cannot be reached
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        scoresFile = scores.read("propane_scores.txt")
        for server in serversToCheck:
            try:
                serverURL = 'http://' + server[1]
                if (enableCustomPorts):
                    for port in portsToCheck:
                        if(port[0] == server[0]):
                            serverURL = serverURL + ":" + port[1]
                print(CheckPostgres(PostgresEnabled, PostgresAddress, PostgresPort, PostgresLogin, PostgresPass, PostgresScore, whiteList, blackList))
                print(bcolors.GREEN + bcolors.BOLD + "Проверяем машину: " + bcolors.RED + server[0] + bcolors.ENDC + " @ " + bcolors.BOLD + server[1] + bcolors.ENDC)
                url = urllib.request.urlopen(serverURL,None,10)
                html = url.read()
                pattern = r'<team>(.*?)</team>'
                team = re.findall(pattern, str(html), re.IGNORECASE)
                team = list(set(team))
                for teams in team:
                    if not len(teams.replace(' ', '')) == 0:
                        teams = teams.replace("_", " ").title().replace(" ", "_")
                        print(bcolors.BOLD + "Машина " + server[0] + bcolors.ENDC + " взломана командой " + bcolors.RED + teams + bcolors.ENDC)
                        for serverAndScore in scoresToAdd:
                            serverScoresection = server[0]+"Scores"
                            if str(server[1]) == str(serverAndScore[0]):
                                if whiteListIsOn and not blackListIsOn:
                                    if teams in whiteList:
                                        if not scores.has_option("TotalScores", teams):
                                            scores.set("TotalScores", teams, 0)
                                        currentScore = scores.getint( "TotalScores",teams)
                                        scores.set( "TotalScores", teams, currentScore+int(serverAndScore[1]))
                                        if not scores.has_option(serverScoresection, teams):
                                            scores.set(serverScoresection, teams, 0)
                                        currentScore = scores.getint( serverScoresection,teams)
                                        scores.set( serverScoresection, teams, currentScore+int(serverAndScore[1]))
                                    else:
                                        print(bcolors.FAIL + bcolors.BOLD + "Команда: " + teams + " не в вайтлисте." + bcolors.ENDC)
                                elif blackListIsOn and not whiteListIsOn:
                                    if teams in blackList:
                                        print(bcolors.FAIL + bcolors.BOLD + "Команда: " + teams + " в блэклисте." + bcolors.ENDC)
                                    else:
                                        if not scores.has_option("TotalScores", teams):
                                            scores.set("TotalScores", teams, 0)
                                        currentScore = scores.getint( "TotalScores",teams)
                                        scores.set( "TotalScores", teams, currentScore+int(serverAndScore[1]))
                                        if not scores.has_option(serverScoresection, teams):
                                            scores.set(serverScoresection, teams, 0)
                                        currentScore = scores.getint( serverScoresection,teams)
                                        scores.set( serverScoresection, teams, currentScore+int(serverAndScore[1]))
                                elif whiteListIsOn and blackListIsOn:
                                    if teams in blackList:
                                        print(bcolors.FAIL + bcolors.BOLD + "Команда: " + teams + " в блэклисте." + bcolors.ENDC)
                                    elif teams in whiteList:
                                        if not scores.has_option("TotalScores", teams):
                                            scores.set("TotalScores", teams, 0)
                                        currentScore = scores.getint( "TotalScores",teams)
                                        scores.set( "TotalScores", teams, currentScore+int(serverAndScore[1]))
                                        if not scores.has_option(serverScoresection, teams):
                                            scores.set(serverScoresection, teams, 0)
                                        currentScore = scores.getint( serverScoresection,teams)
                                        scores.set( serverScoresection, teams, currentScore+int(serverAndScore[1]))
                                    else:
                                        print(bcolors.FAIL + bcolors.BOLD + "Команда: " + teams + " не в вайтлисте." + bcolors.ENDC)
                                else:
                                    if not scores.has_option("TotalScores", teams):
                                        scores.set("TotalScores", teams, 0)
                                    currentScore = scores.getint( "TotalScores",teams)
                                    scores.set( "TotalScores", teams, currentScore+int(serverAndScore[1]))
                                    if not scores.has_option(serverScoresection, teams):
                                        scores.set(serverScoresection, teams, 0)
                                    currentScore = scores.getint( serverScoresection,teams)
                                    scores.set( serverScoresection, teams, currentScore+int(serverAndScore[1]))
            except IOError:
                response = os.system("ping -c 1 " + server[1] + " > /dev/null 2>&1")
                if (response == 0):
                    print(bcolors.GREEN + bcolors.BOLD + "Машина по адресу: " + bcolors.RED + server[0] + bcolors.ENDC + " @ " + bcolors.BOLD + server[1] + bcolors.ENDC + bcolors.GREEN + bcolors.BOLD + " работает!" + bcolors.ENDC)
                else:
                    print(bcolors.FAIL + bcolors.BOLD + server[0] + bcolors.ENDC + " @ " + bcolors.FAIL + bcolors.BOLD + server[1] + bcolors.ENDC + bcolors.FAIL + bcolors.BOLD + " машина не работает!" + bcolors.ENDC)

                try:
                    sock.settimeout(5)
                    if (enableCustomPorts):
                        for port in portsToCheck:
                            if(port[0] == server[0]):
                                sock.connect((server[1], int(port[1])))
                                break
                            else:
                                print(server[0] + " good")
                                break
                    else:
                        sock.connect((server[1], 80))
                    print(bcolors.GREEN + bcolors.BOLD + "Web service for: " + bcolors.RED + server[0] + bcolors.ENDC + " @ " + bcolors.BOLD + server[1] + bcolors.ENDC + bcolors.GREEN + bcolors.BOLD + " is up!" + bcolors.ENDC)
                except socket.error as e:
                    print(bcolors.FAIL + bcolors.BOLD + server[0] + bcolors.ENDC + " @ " + bcolors.FAIL + bcolors.BOLD + server[1] + bcolors.ENDC + bcolors.FAIL + bcolors.BOLD + " web service is down, you may want to check it!" + bcolors.ENDC)
                sock.close()
            except AttributeError:
                print(bcolors.BOLD + "Server " + bcolors.RED + server[0] + bcolors.ENDC + " is not officially " + bcolors.RED + "pwned " + bcolors.ENDC + "yet")
        with open("propane_scores.txt", 'w') as scoresFile:
                scores.write(scoresFile)
        # If backups are are on, make a back up!
        if enableBackUp:
            createBackUp()

'''
initScoreFile():
    Reads the propane_scores file and adds appropriate sections to the score file if they do not exist.
    (Initializes the score file)
'''



def initScoreFile():
        scores.read("propane_scores.txt")
        if not scores.has_section("TotalScores"):
                scores.add_section("TotalScores")

        for server in serversToCheck:
                serverScoresection = server[0]+"Scores"
                if not scores.has_section(serverScoresection):
                        scores.add_section(serverScoresection)


'''
reloadScoreBoard():
    Fetches the score data from the the server list and formats it into an HTML table.
    Also does a second service check to inform users of the servers/service status on the scoreboard.
    The table is returned to be used elsewhere.

    If a section is missing an error is displayed in the console.
'''


def reloadScoreBoard(server):
        print(bcolors.BLUE + bcolors.BOLD + "Обновляем таблицу очков для: " + bcolors.ENDC + bcolors.BOLD + server[0] + bcolors.ENDC)
        try:

            serverScoresection = server[0]+"Scores"
            serverScores = scores.items(serverScoresection)

            #Check if servers and web services are up
            serverStatus = False
            webServerStatus = False
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            response = os.system("ping -c 1 " + server[1] + " > /dev/null 2>&1")
            if (response == 0):
                serverStatus = True
            else:
                serverStatus = False
            try:
                sock.connect((server[1], 80))
                webServerStatus = True
            except socket.error as e:
                webServerStatus = False
            sock.close()

            tableResults = "<div class=\"col-md-12\" id=\"" + server[0] + "\">"
            tableResults = tableResults + "<table class=\"table\" border=\"2\">\n<tr>"
            if (serverStatus and (server[0]).title() != "Total"):
                if (webServerStatus):
                        tableResults = tableResults + "<td colspan=\"2\"><center><h3>" +(server[0]).title() + "</h3><br>Машина: <span style='color:green'>Работает</span><br><br>Веб-сервис: <span style='color:green'>Работает</span><br>"
                else:
                    tableResults = tableResults + "<td colspan=\"2\"><center><h3>" +(server[0]).title() + "</h3><br>Машина: <span style='color:green'>Работает</span><br><br>Веб-сервис: <span style='color:red'>Не работает</span><br>"
            elif (not serverStatus and (server[0]).title() != "Total"):
                if(webServerStatus):
                    tableResults = tableResults + "<td colspan=\"2\"><center><h3>" +(server[0]).title() + "</h3><br>Машина: <span style='color:red'>Не работает</span><br><br>Веб-сервис: <span style='color:green'>Работает</span><br>"
                else:
                    tableResults = tableResults + "<td colspan=\"2\"><center><h3>" +(server[0]).title() + "</h3><br>Машина: <span style='color:red'>Не работает</span><br><br>Веб-сервис: <span style='color:red'>Не работает</span><br>"

            else:
                tableResults = tableResults + "<td colspan=\"2\"><center><h3>" +(server[0]).title() + "</h3><br>"                
            if((server[0]).title() != "Total" and showTargetIP):
                    tableResults = tableResults + "<hr style=\"border-top: 1px solid #000;\"/><h4>Адрес: <span style='color: #fff'>" + server[1]  +"</span></h4>"
            tableResults = tableResults + "</center></td></tr>\n"
            serverScores.sort(key=lambda score: -int(score[1]))
            topTagStart="<div class=\"topscore\">"
            topTagEnd="</div>"
            for team in serverScores:
                tableResults = tableResults + "<tr><td>" + topTagStart + team[0].title() + topTagEnd + "</td><td>" + topTagStart + str(team[1]) +  topTagEnd  + "</td></tr>\n"
                topTagStart="<div class=\"otherscore\">"
                topTagEnd="</div>"
            tableResults = tableResults + "</table></div>"
            return tableResults
        except:
            print(bcolors.FAIL + bcolors.BOLD + "No section for " + server[0] + " (check your template for errors)" + bcolors.ENDC)


'''
getEndTime():
    Calculates the time for left before the game needs to end based on the endtime value in the config file.
    After calculating the timeDelta it will create a countdown.js file. This function is ran during game set up to spawn
    a new Timer thread that will call the endGame() function when the countdown from the timeDelta reaches zero.

    This function is also ran during every main loop iteration to update the countdown timer for the main scoreboard
    that is generated with countdown.js.

'''

def getEndTime(gameSetup):
    currentTime = datetime.now()
    
    try:
        endHour = int(endTime.split(":")[0])
    
        endMinute = int(endTime.split(":")[1])
    except:
        print(bcolors.FAIL + "Странный формат времени у окончания соревнований, нужен 24 часовой формат" + bcolors.ENDC)
    formattedEndTime = currentTime.replace(day=currentTime.day, hour=endHour, minute=endMinute, microsecond=currentTime.microsecond)

    timeDelta = formattedEndTime - currentTime

    if gameSetup:
        endTimer = Timer(timeDelta.seconds, endGame)
        print(bcolors.YELLOW + bcolors.BOLD + "Соревнования закончатся в: " + str(formattedEndTime) + bcolors.ENDC)
        endTimer.start()

    timerJS = """
        function startTimer(duration, display) {
            var timer = duration, hours, minutes, seconds;
                setInterval(function () {
                        hours = parseInt(timer / 3600, 10)
                        minutes = parseInt((timer / 60) % 60, 10)
                        seconds = parseInt(timer % 60, 10);

                        hours = hours < 10 ? "0" + hours : hours;
                        minutes = minutes < 10 ? "0" + minutes : minutes;
                        seconds = seconds < 10 ? "0" + seconds : seconds;

                        
                        
                         display.textContent = "Осталось времени: " + hours + ":" + minutes + ":" + seconds;
                        
                        if(hours <= 0){
                            if(minutes <= 9){
                                display.textContent = "Осталось времени: " + hours + ":" + minutes + ":" + seconds;
                                display.style.color = "red";
                            }else if(minutes >= 10 && minutes <= 30){
                                display.style.color = "orange";
                            }
                        }
                        
                        if (--timer < 0) {
                            timer = duration;
                        }
                    }, 1000);
                }

            window.onload = function () {
                var countdownStart = """ + str(timeDelta.seconds) + """,
                    display = document.querySelector('#countdown');
                        startTimer(countdownStart, display);
                };"""
                
    countdownJS = open(outdir + "countdown.js", "w+")
    countdownJS.write(timerJS)
    countdownJS.close()


'''
endGame():
    3ndG4me r00lz!!!!!!

    This function exits the Propane process, thus, ending the game. This is only called from the Timer thread
    spawned by the getEndTime function when the game set up is first initialized. Once it is called a message
    will output informing the admin that the game has ended, and then will immediately exit the thread and the
    main process.

'''

def endGame():

    print(bcolors.YELLOW + bcolors.BOLD + "Соревнования заканчивается в: " + str(datetime.now()) + bcolors.ENDC)

    os._exit(0)


'''
main():
    Propane main function. Runs the loadConfig(), initScoreFile() functions and then setups up the scoreboard web pages
    by writing them and copying the templates to the directories specified in the propane_config.

    This is an endless loop that constantly scores users, reloads the scoreboard, parses white and black lists, and error corrects itself as needed in
    some cases (e.g. initScoreFile())

    By placing the loadConfig(), initScoreFile(), and score() functions in the loop to run everytime, an administrator can
    live edit the config, and score files as needed.

    Plugins (Propane Accessories) are loaded in a for loop which initializes and runs the main function of every plugin.

    The core functionality of the main is to run the entire scoreboard and connect all the pieces, and write them out to the
    scoreboard file that is specified by the outfile variable.

    Any start or end time delays and their resulting effects (i.e. countdown timer on the scoreboard) are parsed and calculated.
    Evey iteration the getEndTime will update the coutdown timer on the scoreboard.

    The delay interval set by the time value loaded into the time global variable determines how often the scoreboard executes
    its operations.
'''

def main():

        global gameSetup


        while True:

                # Load Conifgurations
                loadConfig()
                # Init Score File
                initScoreFile()
                #Refresh Countdown Timer
                if endTime and not gameSetup:
                    getEndTime(gameSetup)
                # Open template file
                templateFile = open("template/scoreboard.html", 'r')
                serversFile = open("template/template.html", 'r')
                # Read in template file
                scorePage = templateFile.read()
                serversPage = serversFile.read()
                # Load up the white list
                whiteList = ""

                for user in whiteListInit:
                    parseWhiteList = csv.reader([user[1]])
                    for user in parseWhiteList:
                        whiteList = user
                
                blackList = ""

                for user in blackListInit:
                    parseBlackList = csv.reader([user[1]])
                    for user in parseBlackList:
                        blackList = user

               

                # Do one-time set up stuff on start of the game
                if(gameSetup):
                        print(bcolors.CYAN + bcolors.BOLD + "Настройка игры: " + bcolors.ENDC + " копирование шаблонных файлов")
                        copytree("template", outdir, dirs_exist_ok=True)
                        os.remove(outdir + "template.html")

                        if startTime:
                            currentTime = datetime.now()

                            try:
                                startHour = int(startTime.split(":")[0])
                                startMinute = int(startTime.split(":")[1])
                            except ValueError:
                                print(bcolors.FAIL + "Какой-то странный формат времени..." + bcolors.ENDC)
                        
                            formattedStartTime = currentTime.replace(day=currentTime.day, hour=startHour, minute=startMinute, microsecond=currentTime.microsecond)

                            timeDelta = formattedStartTime - currentTime

                            print(bcolors.GREEN + bcolors.BOLD + "Соревнования начнутся в: " + str(formattedStartTime) + bcolors.ENDC)
                            time.sleep(timeDelta.seconds)

                        if endTime:
                            
                            getEndTime(gameSetup)
                            
                        gameSetup = False
                        
                # Do some scoring!
                score(whiteList, blackList)

                #Load Propane Accessories and run their start() function
                if enablePropAcc:
                    for i in loadPropAcc():
                        print(bcolors.CYAN + bcolors.BOLD + "Loading Propane Accessory: " + bcolors.ENDC + bcolors.BOLD + i["name"] + bcolors.ENDC)
                        propacc = initPropAcc(i)
                        propacc.start()

                # Update Server Scores on Scoreboard

                # Grab all hosts after their status checks and create a list of those hosts.
                allHosts = []
                for server in serversToCheck:
                    thisTable = reloadScoreBoard(server)
                    # Append host to list of host and wrap it in a div container that will manage the layout
                    print(bcolors.GREEN + bcolors.BOLD + "Обновляем " + bcolors.ENDC + bcolors.BOLD + server[0] + bcolors.ENDC + " тэг в шаблоне")
                    allHosts.append("<div class='col-md-3 col-xs-6'>" + thisTable + "</div>")
                # Defined a string that will append all the dynamically generated target HTML data and convert it to a string as it iterates each host.
                hostTemplateString = ""
                for host in allHosts:
                    hostTemplateString += host
                # Grab the <SERVERS> tag to replace in the template.
                serverLabelTag="<SERVERS>"
                print(bcolors.GREEN + bcolors.BOLD + "Обновляем " + bcolors.ENDC + bcolors.BOLD + serverLabelTag + bcolors.ENDC + " тэг в шаблоне")
                # Replace <SERVERS> with the generated targets string.
                scorePage = scorePage.replace(serverLabelTag,hostTemplateString)
                # Update Total Scores on Scoreboard
                thisTable = reloadScoreBoard(["Total",""])
                serverLabelTag=("<TOTAL>").upper()
                print(bcolors.GREEN + bcolors.BOLD + "Обновляем " + bcolors.ENDC + bcolors.BOLD + serverLabelTag + bcolors.ENDC + " тэг в шаблоне")
                serversPage = serversPage.replace(serverLabelTag,thisTable)
                # Write out the updates made to the Scoreboard and get ready for next interval
                print(bcolors.BLUE + bcolors.BOLD + "Обновляем таблицу очков " + bcolors.ENDC + bcolors.BOLD + outfile + bcolors.ENDC)
                outFileHandler = open(outfile, 'w')
                outFileHandler.write(scorePage)
                outFileHandler.close()
                print(bcolors.BLUE + bcolors.BOLD + "Обновляем таблицу очков " + bcolors.ENDC + bcolors.BOLD + outfile2 + bcolors.ENDC)
                outFileHandler = open(outfile2, 'w')
                outFileHandler.write(serversPage)
                outFileHandler.close()
                print(PostgresEnabled)

                print(bcolors.CYAN + bcolors.BOLD + "Следующее обновление через: " + bcolors.ENDC + str(sleepTime) + bcolors.BOLD + " секунд" + bcolors.ENDC)
                time.sleep(sleepTime)



#Execute main()

if __name__ == "__main__":
    ascii_art = '''
     _______. __  .______        _______.     ___      __    __  
    /       ||  | |   _  \      /       |    /   \    |  |  |  | 
   |   (----`|  | |  |_)  |    |   (----`   /  ^  \   |  |  |  | 
    \   \    |  | |   _  <      \   \      /  /_\  \  |  |  |  | 
.----)   |   |  | |  |_)  | .----)   |    /  _____  \ |  `--'  | 
|_______/    |__| |______/  |_______/    /__/     \__\ \______/                                                            
    '''
    print(bcolors.CYAN + bcolors.BOLD + ascii_art + bcolors.ENDC)

    main()


#TODO Новые поля в конфиге: Включён ли модуль (Тру фолс), Адрес постгреса, порт для него, логин, пароль, количество очков которые будут сниматься DONE
#TODO Через SQLAlchemy чекаем таблицу apts, получаем названия команд которые там содержатся DONE
#TODO Смотрим находятся ли они в вайтлиисте, убираем повторы
#TODO После этого минусуем им баллы, сделать ли это всё отдельной функцией
#TODO Вывод постгреса на веб
