"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import json
import re
from urllib2 import urlopen
from json import load
import datetime


class theData():
    
    def __init__(self, x):
### Defines all global variables
        self.megaList = [0]*239
        self.theDate = {}
        self.count = 0
        self.key = 'XXXXXX'
        self.zippy = x
        self.zippy = str(self.zippy)
### Automatic IP, key inserted, 10 day hourly URL for weather
        self.url = 'http://api.wunderground.com/api/'+self.key
        self.url += '/hourly10day/q/'
        self.url += self.zippy
        self.url += '.json'
        self.output = urlopen(self.url)
        self.json_obj = load(self.output)
        


### Place holder for a method to change your JSON data
    def change_url(self): ##Returns a URL to weather undergrounds API
        url = 'http://api.wunderground.com/api/'+self.key
        url += '/hourly10day/q'
        url += '/autoip.json'
        return url


### Parses JSON
    def parse_json_beta(self): 
        for oneday in self.json_obj['hourly_forecast']:
            x ={
                'day':str((self.json_obj)['hourly_forecast'][self.count]['FCTTIME']['mday_padded']),
                'hour': str((self.json_obj)['hourly_forecast'][self.count]['FCTTIME']['hour_padded']),
                'condition':str((self.json_obj)['hourly_forecast'][self.count]['condition']),
                'month':str((self.json_obj)['hourly_forecast'][self.count]['FCTTIME']['mon_padded']),
                'humidity' :str((self.json_obj)['hourly_forecast'][self.count]['humidity']),
                'temperature' :str((self.json_obj)['hourly_forecast'][self.count]['temp']['english']),
                'uvi'      :str((self.json_obj)['hourly_forecast'][self.count]['uvi'])
                }
        return x

### Creates a list, consisting of dictionaries parsed from the json (See method 'parse_json_beta')
    def makeWeek(self):
        for i in range(239):
            self.megaList[i] = theData.parse_json_beta(self)
            self.count += 1
        return self.megaList
        
        

    def establishDate(self): ##returns the day of the year
        self.theDate['day'] = str((self.json_obj)['hourly_forecast'][0]['FCTTIME']['mday_padded'])
        self.theDate['month'] = str((self.json_obj)['hourly_forecast'][0]['FCTTIME']['mon_padded'])
        self.theDate['year'] = str((self.json_obj)['hourly_forecast'][0]['FCTTIME']['year'])
        self.theDate['hour'] = str((self.json_obj)['hourly_forecast'][0]['FCTTIME']['hour_padded'])
        return self.theDate

    
### Creates a writable handle called wHandle
    def createWriteHandle(self): 
        x = raw_input('Name your Json')
        jsonHandle = open(x,'w')
        return jsonHandle

   
    def makeToday(self):
        today =  self.megaList[0]['day']  #Str
        todaysForecast = []
        for x in  self.megaList:
            if x['day'] == today:
                todaysForecast.append(x)
            else:
                return todaysForecast

    def makeTomorrow(self):
        tomorrow = int( self.megaList[0]['day'])+1
        tomorrowsForecast = []
        for x in  self.megaList:
            if int(x['day']) == tomorrow:
                tomorrowsForecast.append(x)
                try: continue
                except: break
        return tomorrowsForecast
    
    def seperateLists(self):
        today =  self.megaList[0]['day']
        tomorrow = int( self.megaList[0]['day'])+1
        todaysForecast = []
        tomorrowsForecast = []
        for x in  self.megaList:
            if x['day'] == today:
                todaysForecast.append(x)
            elif int(x['day']) == tomorrow:
                tomorrowsForecast.append(x)
            else:
                break
        return todaysForecast,tomorrowsForecast
        
class Choices(theData):
    
    ### Start
    def __init__(self,o,p,userZip):
        
        ### Initialize parent class
        self.data = theData(userZip)
        self.listUsing = self.data.makeWeek()
        self.hours = str(p)
        ### We have the week, lets parse it into today or tomorrow, or no parse
        self.timeframe = str(o)
        if self.timeframe == 'today':
            self.listUsing = self.data.makeToday()
        if self.timeframe == 'tomorrow':
            self.listUsing = self.data.makeTomorrow()
        self.usableHours = self.parse_list_for_user_hours()

        ### Acceptable Weather conditions other than clear
        self.acceptableConditions = ['Patches of Fog','Shallow Fog','Partial Fog','Overcast','Partly Cloudy', 'Mostly Cloudy','Scattered Clouds']

        ###Phase 2
        
        self.sunnySkies,self.cloudyConditions = self.outdoor_conditions()

        self.highestTemp, self.warmestHour = self.get_highest_temp()
        try:
            self.highestTempSunny = self.get_highest_temp_sunny()
        except:
            pass
        try:
            self.highestTempCloudy = self.get_highest_temp_cloudy()
        except:
            pass
        try:
            self.lowestUviSunny = self.get_lowest_uvi_sunny()
        except:
            pass
        try:
            self.lowestUviCloudy = self.get_lowest_uvi_cloudy()
        except:
            pass
        ### Phase 3

        try:
            self.optimalTimes = self.optimal_choices()
        except:
            print ('failed establishing optimal choices')
        try:
            self.secondaryTimes = self.secondary_choices()
        except:
            pass
        ###Final Phase 4

        #self.first_sunnyz,y = x.final_filter_early()

        #p, q = x.final_filter_late()
        
    ###
    def return_data(self):
            return self.usableHours


    
    ###Function that will parse the given list by hour, tailored to the user's daylight hours.
    def parse_list_for_user_hours(self):
        self.start, self.end, self.usableHours = int(self.hours[0:2]), int(self.hours[3:5]),[]
        for x in self.listUsing:
            if int(x['hour']) < self.start or int(x['hour']) > self.end:
                self.listUsing.remove(x)
            else:
                self.usableHours.append(x)
        return self.usableHours


    ### Lets parse some more lists starting with condition, we'll filter out other things later
    ### Two lists, clear skies, and cloudy/misty
    def outdoor_conditions(self):
        self.sunnySkies = []
        self.cloudyConditions = []
        for x in self.usableHours:
            if x['condition'] == 'Clear':
                self.sunnySkies.append(x)
            else:
                for y in self.acceptableConditions:
                    if x['condition'] == y:
                        self.cloudyConditions.append(x)
                    else:
                        continue
        return self.sunnySkies, self.cloudyConditions




    ### Get highest temps and lowest Uvi's - Condense later Dont repeat yourself, but just maybe this once
    def get_highest_temp(self):
        self.highestTemp = 0
        for x in self.usableHours:
            if int(x['temperature']) > self.highestTemp:
                self.highestTemp = int(x['temperature'])
                self.warmestHour = int(x['hour'])
        return self.highestTemp, self.warmestHour
    
    def get_highest_temp_sunny(self):
        self.highestTempSunny = int(self.sunnySkies[0]['temperature'])
        for x in self.sunnySkies:
            if int(x['temperature']) > self.highestTempSunny:
                self.highestTempSunny = int(x['temperature'])
        return self.highestTempSunny

    def get_highest_temp_cloudy(self):
        self.highestTempCloudy = int(self.cloudyConditions[0]['temperature'])
        for x in self.cloudyConditions:
            if int(x['temperature']) > self.highestTempCloudy:
                self.highestTempCloudy = int(x['temperature'])
        return self.highestTempCloudy

    def get_lowest_uvi_sunny(self):
        self.lowestUviSunny = int(self.sunnySkies[0]['uvi'])
        for x in self.sunnySkies:
            if int(x['uvi']) < self.lowestUviSunny:
                self.lowestUvi = int(x['uvi'])
        return self.lowestUviSunny

    def get_lowest_uvi_cloudy(self):
        self.lowestUviCloudy = int(self.cloudyConditions[0]['uvi'])
        for x in self.cloudyConditions:
            if int(x['uvi']) < self.lowestUviCloudy:
                self.lowestUvi = int(x['uvi'])
        return self.lowestUviCloudy
    
   
        
### What do I have so far....Lists of clear and cloudy hours we can use, I have highest temps of those 2 and lowest uvis        
## What I want to do, two lists, optimal, clear skies parsed by within 10 temp, then lowest UV
    
    def optimal_choices(self):
        self.tempTimes = []
        self.optimalTimes = []
        for x in self.sunnySkies:
            if int(x['temperature']) >= self.highestTempSunny-5 and int(x['temperature']) >= self.highestTemp-10:
                self.tempTimes.append(x)
        if self.tempTimes == []:
            for L in self.sunnySkies:
                if int(L['temperature']) >= self.highestTempSunny-5:
                    self.tempTimes.append(L)
        for y in self.tempTimes:
            if int(y['uvi']) == self.lowestUviSunny:
                    self.optimalTimes.append(y)
            elif int(y['uvi']) <= self.lowestUviSunny+1:
                    self.optimalTimes.append(y)
            elif int(y['uvi']) <= self.lowestUviSunny+2:
                self.optimalTimes.append(y)
            elif int(y['uvi']) <= self.lowestUviSunny+3:
                self.optimalTimes.append(y)
        if self.optimalTimes == []:
            self.optimalTimes = self.tempTimes
        return self.optimalTimes

    def secondary_choices(self):
        self.stempTimes = []
        self.secondaryTimes = []
        for x in self.cloudyConditions:
            if int(x['temperature']) >= self.highestTempCloudy-5 and int(x['temperature']) >= self.highestTemp-10:
                self.stempTimes.append(x)
        if self.stempTimes == []:
            for T in self.cloudyConditions:
                if int(T['temperature']) >= self.highestTempCloudy-5:
                    self.stempTimes.append(T)
        for y in self.stempTimes:
            if int(x['uvi']) == self.lowestUviCloudy:
                    self.secondaryTimes.append(y)
            elif int(x['uvi']) <= self.lowestUviCloudy+1 and int(x['uvi']) >= self.lowestUviCloudy-1:
                    self.secondaryTimes.append(y)
            elif int(x['uvi']) <= self.lowestUviCloudy+2 and int(x['uvi']) >= self.lowestUviCloudy-2:
                self.secondaryTimes.append(y)
            elif int(x['uvi']) <= self.lowestUviCloudy+3 and int(x['uvi']) >= self.lowestUviCloudy-3:
                self.secondaryTimes.append(y)
            else:
                self.secondaryTimes = self.stempTimes
        return self.secondaryTimes
            
            
    def final_filter_early(self):
        self.finalSunny = []
        self.finalCloudy = []
        self.reference = 9999
        for x in self.optimalTimes:
            if int(x['hour']) < self.reference:
                self.finalSunny.append(x)
            self.reference = int(x['hour'])
        self.reference2 = 999
        for y in self.secondaryTimes:
            if int(y['hour']) < self.reference2:
                self.finalCloudy.append(y)
            self.reference2 = int(y['hour'])
        return self.finalSunny, self.finalCloudy

    def final_filter_late(self):
        self.finalSunny = []
        self.finalCloudy = []
        self.reference = 0
        for x in self.optimalTimes:
            if int(x['hour']) > self.reference:
                self.finalSunny.append(x)
            self.reference = int(x['hour'])
        self.reference2 = 0
        for y in self.secondaryTimes:
            if int(y['hour']) > self.reference2:
                self.finalCloudy.append(y)
            self.reference2 = int(y['hour'])
        return self.finalSunny, self.finalCloudy






def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
        'amzn1.echo-sdk-ams.app.9b5a0dcf-0953-4f5f-a016-2144736d41fc'):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])
        print ('lalalal')
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    
    if intent_name == "AMAZON.HelpIntent":
        return experiment2()
    elif intent_name == "MyDesire":
        return experiment(intent,session)
    elif intent_name == "MyDesiree":
        return alternative(intent,session)
    elif intent_name == "AMAZON.RepeatIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.StopIntent":
        return end_it()
    elif intent_name == "AMAZON.CancelIntent":
        return end_it()
    elif intent_name == "trashGather":
        return messed_up()
    ###Lets GET BUSY
    else:
        return get_welcome_response()


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------
def experiment(intent,session):
    try:
        print (intent['slots'])
        session_attributes = {}
        userZip = intent['slots']['DesiredZipCode']['value']
    
        userTime1 = intent['slots']['DesiredTimeOne']['value']
        userTime1 = str(userTime1)
        userTime1 = userTime1[0:2]
    
        userTime2 = intent['slots']['DesiredTimeTwo']['value']
        userTime2 = str(userTime2)
        userTime2 = userTime2[0:2]
    
        userTime = userTime1+':'+userTime2
        userDay = intent['slots']['DesiredDay']['value']
    

        choicesMade = Choices(userDay,userTime,userZip)
        L = choicesMade.warmestHour
        earlySunny,earlyCloudy = choicesMade.final_filter_early()
        latestSunny, latestCloudy = choicesMade.final_filter_late()
    
        x = 'trollop'
        try:
            if choicesMade.optimalTimes != []:
                print ('test1')
                earlySunnyHour = str(earlySunny[0]['hour'])
                earlySunnyMonth = str(earlySunny[0]['month'])
                earlySunnyDay = str(earlySunny[0]['day'])
                earlySunnyTemp = str(earlySunny[0]['temperature'])
                earlySunnyCond = str(earlySunny[0]['condition'])
                lateSunnyHour = str(latestSunny[-1]['hour'])
                lateSunnyTemp = str(latestSunny[-1]['temperature'])
                lateSunnyCond = str(latestSunny[-1]['condition'])
                lateSunnyMonth = str(latestSunny[-1]['month'])
                lateSunnyDay = str(latestSunny[-1]['day'])
                x = 'For '+userDay+', the earliest optimal time to go outside would be the <say-as interpret-as="ordinal">'+earlySunnyHour + '</say-as> hour , on <say-as interpret-as="date">????'+ earlySunnyMonth  + earlySunnyDay  +'</say-as>' + ' with a temperature of ' + earlySunnyTemp + ', degrees and a condition of ,' + earlySunnyCond
                x += ', the latest optimal time to go outside would be the <say-as interpret-as="ordinal">'+lateSunnyHour + '</say-as> hour , on <say-as interpret-as="date">????'+ lateSunnyMonth  + lateSunnyDay  +'</say-as>' + ', with a temperature of ' + lateSunnyTemp + ' degrees, and a condition of ,' + lateSunnyCond
                y = 'For '+userDay+', the earliest optimal time to go outside would be '+earlySunnyHour + ':00, on ' +earlySunnyMonth  +'/'+ earlySunnyDay  + ' with a temperature of ' + earlySunnyTemp + ', degrees and a condition of ,' + earlySunnyCond
                y += ', the latest optimal time to go outside would be '+lateSunnyHour + ':00 , on '+ lateSunnyMonth  +'/' +lateSunnyDay  + ', with a temperature of ' + lateSunnyTemp + ' degrees, and a condition of ,' + lateSunnyCond
            elif choicesMade.optimalTimes == [] and choicesMade.secondaryTimes != []:
                print ('hi were up to here')
                earlyCloudyHour = str(earlyCloudy[0]['hour'])
                earlyCloudyMonth = str(earlyCloudy[0]['month'])
                earlyCloudyDay = str(earlyCloudy[0]['day'])
                earlyCloudyTemp = str(earlyCloudy[0]['temperature'])
                earlyCloudyCond = str(earlyCloudy[0]['condition'])
                lateCloudyHour = str(latestCloudy[-1]['hour'])
                lateCloudyTemp = str(latestCloudy[-1]['temperature'])
                lateCloudyCond = str(latestCloudy[-1]['condition'])
                lateCloudyMonth = str(latestCloudy[-1]['month'])
                lateCloudyDay = str(latestCloudy[-1]['day'])
        
                x = 'For '+userDay+', the earliest optimal time to go outside would be the <say-as interpret-as="ordinal">'+ earlyCloudyHour + '</say-as> hour, on <say-as interpret-as="date">????'+ earlyCloudyMonth  + earlyCloudyDay  +'</say-as>' + ' with a temperature of ' + earlyCloudyTemp + ', degrees and a condition of ,' + earlyCloudyCond
                x += ', the latest optimal time to go outside would be the <say-as interpret-as="ordinal">'+lateCloudyHour + '</say-as> hour , on <say-as interpret-as="date">????'+ lateCloudyMonth  + lateCloudyDay  +'</say-as>' + ', with a temperature of ' + lateCloudyTemp + ', degrees and a condition of ,' + lateCloudyCond
                y = 'For '+userDay+', the earliest optimal time to go outside would be '+earlyCloudyHour + ':00, on ' +earlyCloudyMonth  +'/'+ earlyCloudyDay  + ' with a temperature of ' + earlyCloudyTemp + ', degrees and a condition of ,' + earlyCloudyCond
                y += ', the latest optimal time to go outside would be '+lateCloudyHour + ':00 , on '+ lateCloudyMonth  +'/' +lateCloudyDay  + ', with a temperature of ' + lateCloudyTemp + ' degrees, and a condition of ,' + lateCloudyCond
            
            else:
                x = 'toil'
                y = 'trouble'
        except:
            x = 'toil'
            y = 'trouble'
        if x == 'toil':
            x = 'No optimal weather conditions could be established, this may be from inclimate weather conditions, incorrect time frame, or incorrect zipcode.'
            y = 'No optimal weather conditions could be established, this may be from inclimate weather conditions, incorrect time frame, or incorrect zipcode.'
        card_title = 'zipcode'
    except:
        card_title = 'Woops'
        x = 'I may have misheard you, try again or ask for help'
        y = 'Asking for help is easy, just say alexa help me'
    ###Lets make values for our speech here
    speech_output = '<speak>'+x+'</speak>'
    
    reprompt_text = y
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def alternative(intent,session):
    try:
        y = 'Asking for help is easy, just say Alexa help me'
        session_attributes = {}
        userZip = intent['slots']['easyCode']['value']

    
        userTime = '07:21'
        userDay = intent['slots']['easyDay']['value']

        choicesMade = Choices(userDay,userTime,userZip)

        L = choicesMade.warmestHour
        earlySunny,earlyCloudy = choicesMade.final_filter_early()
        latestSunny, latestCloudy = choicesMade.final_filter_late()

        x = 'trollop'
        try:
            if choicesMade.optimalTimes != []:
                print ('test1')
                earlySunnyHour = str(earlySunny[0]['hour'])
                earlySunnyMonth = str(earlySunny[0]['month'])
                earlySunnyDay = str(earlySunny[0]['day'])
                earlySunnyTemp = str(earlySunny[0]['temperature'])
                earlySunnyCond = str(earlySunny[0]['condition'])
                lateSunnyHour = str(latestSunny[-1]['hour'])
                lateSunnyTemp = str(latestSunny[-1]['temperature'])
                lateSunnyCond = str(latestSunny[-1]['condition'])
                lateSunnyMonth = str(latestSunny[-1]['month'])
                lateSunnyDay = str(latestSunny[-1]['day'])
                print ('test2')
                x = 'For '+userDay+', the earliest optimal time to go outside would be the <say-as interpret-as="ordinal">'+earlySunnyHour + '</say-as>hour , on <say-as interpret-as="date">????'+ earlySunnyMonth  + earlySunnyDay  +'</say-as>' + ' with a temperature of ' + earlySunnyTemp + ', degrees and a condition of ,' + earlySunnyCond
                x += ', the latest optimal time to go outside would be the <say-as interpret-as="ordinal">'+lateSunnyHour + '</say-as> hour , on <say-as interpret-as="date">????'+ lateSunnyMonth  + lateSunnyDay  +'</say-as>' + ', with a temperature of ' + lateSunnyTemp + ' degrees, and a condition of ,' + lateSunnyCond
                y = 'For '+userDay+', the earliest optimal time to go outside would be '+earlySunnyHour + ':00, on ' +earlySunnyMonth  +'/'+ earlySunnyDay  + ' with a temperature of ' + earlySunnyTemp + ', degrees and a condition of ,' + earlySunnyCond
                y += ', the latest optimal time to go outside would be '+lateSunnyHour + ':00 , on '+ lateSunnyMonth  +'/' +lateSunnyDay  + ', with a temperature of ' + lateSunnyTemp + ' degrees, and a condition of ,' + lateSunnyCond
                print ('test3')
            elif choicesMade.optimalTimes == [] and choicesMade.secondaryTimes != []:
                print ('hi were up to here')
                earlyCloudyHour = str(earlyCloudy[0]['hour'])
                earlyCloudyMonth = str(earlyCloudy[0]['month'])
                earlyCloudyDay = str(earlyCloudy[0]['day'])
                earlyCloudyTemp = str(earlyCloudy[0]['temperature'])
                earlyCloudyCond = str(earlyCloudy[0]['condition'])
                lateCloudyHour = str(latestCloudy[-1]['hour'])
                lateCloudyTemp = str(latestCloudy[-1]['temperature'])
                lateCloudyCond = str(latestCloudy[-1]['condition'])
                lateCloudyMonth = str(latestCloudy[-1]['month'])
                lateCloudyDay = str(latestCloudy[-1]['day'])
        
                x = 'For '+userDay+', the earliest optimal time to go outside would be the <say-as interpret-as="ordinal">'+ earlyCloudyHour + ' hour </say-as> , on <say-as interpret-as="date">????'+ earlyCloudyMonth  + earlyCloudyDay  +'</say-as>' + ' with a temperature of ' + earlyCloudyTemp + ', degrees and a condition of ,' + earlyCloudyCond
                x += ', the latest optimal time to go outside would be the <say-as interpret-as="ordinal">'+lateCloudyHour + '</say-as> hour , on <say-as interpret-as="date">????'+ lateCloudyMonth  + lateCloudyDay  +'</say-as>' + ', with a temperature of ' + lateCloudyTemp + ', degrees and a condition of ,' + lateCloudyCond
                y = 'For '+userDay+', the earliest optimal time to go outside would be '+earlyCloudyHour + ':00, on ' +earlyCloudyMonth  +'/'+ earlyCloudyDay  + ' with a temperature of ' + earlyCloudyTemp + ', degrees and a condition of ,' + earlyCloudyCond
                y += ', the latest optimal time to go outside would be '+lateCloudyHour + ':00 , on '+ lateCloudyMonth  +'/' +lateCloudyDay  + ', with a temperature of ' + lateCloudyTemp + ' degrees, and a condition of ,' + lateCloudyCond
            else:
                x = 'toil'
        except:
            x = 'toil'
        if x == 'toil':
            x = 'No optimal weather conditions could be established, this may be from inclimate weather conditions, incorrect time frame, or incorrect zipcode.'
            y = 'No optimal weather conditions could be established, this may be from inclimate weather conditions, incorrect time frame, or incorrect zipcode.'
    except:
        x = 'You have confused me, try again or ask for help'
    
        
    card_title = 'Your results'
    
    ###Lets make values for our speech here
    speech_output = '<speak>'+x+'</speak>'
    
    reprompt_text = y
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))



def experiment2():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "Welcome"
    speech_output = '<speak>Ask clear skies for the best weather for today, tomorrow, or this week followed by your zipcode</speak>'
  
    # If the user either does not reply to the welcome message or says something
    # that is not understood, thesy will be prompted again with this text.
    reprompt_text = 'If you were confused, just say easy set, followed by your zipcode followed by the words, for today, for tomorrow or this week'
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))



def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = '<speak> Try asking clear skies for the most optimal times to go outside for either today, tomorrow or this week, followed by your zipcode.</speak>'
    
  
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = 'If you need more help, just ask!'
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def end_it():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Goodbye!"
    speech_output = '<speak> Hope you enjoyed Clear Skies weather! Toodles </speak>'
    
  
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = None
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def messed_up():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    print ('lalalal12')
    session_attributes = {}
    card_title = "You may have confused Alexa"
    speech_output = '<speak> Try asking alexa for the best weather in your zipcode for either today, tomorrow, or this week </speak>'
    
    print ('lalalal21')
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = 'An example phrase would be, for today my zipcode is one one, two one, five'
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def set_time_in_session(intent, session):
    '''Sets the start time for the session and preapres teh speech to reply to the user'''
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    
    if 'time' in intent ['slots']:
        start_time = intent['slots']['time']['value']
        session_attributes = create_start_time_attributes(start_time)
        speech_output = "Starting at your current time " + start_time
        reprompt_text = None
    else:
        speech_output = "This is a placeholder"
        reprompt_text = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


    
def create_start_time_attributes(start_time):
    return {"startTime": start_time}


# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': reprompt_text
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
