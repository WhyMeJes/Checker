#!/usr/local/bin/python
"""
This is 3ndG4me and Myntal's automated scoring code for the Propane game.

Right now this is literally a rip-off of NetKotH written by Irongeek, so praise be to Irongeek.

CURRENTLY PROPANE IS very much a WIP. It will work the same as NetKotH at base level, but we plan
to give it a face lift, and add some new functionality.

We <3 NetKotH

Create a propane_config.ini in the same directory as the script
to look something like:
______________________________________________________________
[General]
outfile = default.htm
sleeptime = 6

[Servers To Check]
linux = http://127.0.0.1/a.htm
windows = http://127.0.0.1/b.htm
wildcard = http://127.0.0.1/c.htm
______________________________________________________________
Server names can be changed (no ":" or "=" characters please),
and the score file will be generated by the script. I'm just now
learning Python, so I'm sure there are better ways to do some
of the tasks I do in this script. You can also make a
template.htm file, and tags that match the server name in all
upper case will be replaced with the score information for that
box.

"""
import urllib2
import urllib
import re
import ConfigParser
import time
from distutils.dir_util import copy_tree
import os

#------Make some globals
config = ConfigParser.RawConfigParser()
scores = ConfigParser.RawConfigParser()
configfile =""
serverstocheck = ""
sleeptime = ""
outfile = ""
outdir = ""
gameSetup = True

def getsettings():
        print "Grabbing settings"
        global configfile, serverstocheck, sleeptime, outfile, outdir
        configfile = config.read("propane_config.ini")
        serverstocheck = config.items("Servers To Check")
        sleeptime = config.getint("General", "sleeptime")
        outfile = config.get("General", "outfile")
        outdir = config.get("General", "outdir")

def checkpagesandscore():
        scoresfile = scores.read("propane_scores.txt")
        for server in serverstocheck:
            try:
                print "About to check server " + server[0] + " " + server[1]
                url = urllib2.urlopen(server[1],None,10)
                #url = urllib2.urlopen(server[1])
                html = url.read()
                team = re.search('<team>(.*)</team>', html, re.IGNORECASE).group(1).strip().replace("=","").replace("<","").replace(">","")
                print "Server " + server[0] + " owned by " + team
                serverscoressection = server[0]+"Scores"
                if not scores.has_option("TotalScores", team):
                    scores.set("TotalScores", team, 0)
                currentscore = scores.getint( "TotalScores",team)
                scores.set( "TotalScores", team, currentscore+1)
                if not scores.has_option(serverscoressection, team):
                    scores.set(serverscoressection, team, 0)
                currentscore = scores.getint( serverscoressection,team)
                scores.set( serverscoressection, team, currentscore+1)
            except IOError:
                print server[0] + " " + server[1] + " may be down, skipping it"
            except AttributeError:
                print server[0] + " may not be owned yet"
        with open("propane_scores.txt", 'wb') as scoresfile:
                scores.write(scoresfile)

def makescoresections():
        scoresfile = scores.read("propane_scores.txt")
        if not scores.has_section("TotalScores"):
                scores.add_section("TotalScores")

        for server in serverstocheck:
                serverscoressection = server[0]+"Scores"
                if not scores.has_section(serverscoressection):
                        scores.add_section(serverscoressection)

def maketables(server):
        print "Making score table for " + server[0]
        try:
            serverscoressection = server[0]+"Scores"
            serverscores = scores.items(serverscoressection)
            tableresults = "<div id=\"" + server[0] + "\">"
            tableresults = tableresults + "<table border=\"2\">\n<tr>"
            tableresults = tableresults + "<td colspan=\"2\"><center><b class=\"scoretabletitle\">" +(server[0]).title() + "</b><br>"
            tableresults = tableresults + "<a href=\"" + server[1] + "\">" + server[1]  +"</a>"
            tableresults = tableresults + "</center></td>"
            tableresults = tableresults + "</tr>\n"
            serverscores.sort(key=lambda score: -int(score[1]))
            toptagstart="<div class=\"topscore\">"
            toptagend="</div>"
            for team in serverscores:
                tableresults = tableresults + "<tr><td>" + toptagstart + team[0].title() + toptagend + "</td><td>" + toptagstart + str(team[1]) +  toptagend  + "</td></tr>\n"
                toptagstart="<div class=\"otherscore\">"
                toptagend="</div>"
            tableresults = tableresults + "</table></div>"
            return tableresults
        except:
            print "No section for " + server[0]
#------Main begin

while 1:
        #------Check files that may have changed since las loop
        getsettings() #-------Grab core config values, you have the option to edit config file as the game runs
        makescoresections() #In case score setions for a bax are not there
        templatefilehandle = open("template/template.html", 'r')
        scorepagestring=templatefilehandle.read()
        #------Look at all the pages to see who owns them.
        checkpagesandscore()

        if(gameSetup):
                copy_tree("template", outdir)
                os.remove(outdir + "template.html")
                gameSetup = False

        #------Make Tables
        for server in serverstocheck:
            thistable = maketables(server)
            serverlabeltag=("<" + server[0] + ">").upper()
            print "Searching for " + serverlabeltag + " tag to replace in template.html (case sensitive)"
            scorepagestring = scorepagestring.replace(serverlabeltag,thistable)
        #------Make Total Table
        thistable = maketables(["Total",""])
        serverlabeltag=("<TOTAL>").upper()
        print "Searching for " + serverlabeltag + " to replace (case sensitive)"
        scorepagestring = scorepagestring.replace(serverlabeltag,thistable)
        #------Making the score page
        print "Writing " + outfile
        outfilehandle = open(outfile, 'w')
        outfilehandle.write(scorepagestring)
        outfilehandle.close()
        print "Sleeping for " + str(sleeptime)
        time.sleep(sleeptime)
#------Main end