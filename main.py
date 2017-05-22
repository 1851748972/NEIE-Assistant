#!/usr/bin/python
#coding=utf-8
import sys, os, time, random, json, argparse
import xml.etree.ElementTree as ET
sys.path.append(os.getcwd() + '/library')
import requests, library

class learn_english:
    def __init__(self, path, username, password, level):
        self.path = path
        self.username = username
        self.password = password
        self.level = level
        self.available = 0

    def __encode_object(self, obj):
        for name in obj:
            obj[name] = library.encode(obj[name])
        return obj

    def __decode_object(self, obj):
        for name in obj:
            obj[name] = library.decode(obj[name])
        return obj

    def __xml(self, method, head, data):
        xml = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <CredentialSoapHeader xmlns="http://www.open.com.cn">
'''
        xml += '      <Username>' + head['Username'] + '</Username>\n'
        xml += '      <Password>' + head['Password'] + '</Password>\n'
        xml += '''      <ClientCredential>83BCC79913F2331685F4851C4ED2DA72  E37438347941F22F6A873D18CE562AC9</ClientCredential>
    </CredentialSoapHeader>
  </soap:Header>
  <soap:Body>
'''
        xml += '    <' + method + ' xmlns="http://www.open.com.cn">\n'
        for name in data:
            xml += '      <' + name + '>' + data[name] + '</' + name + '>\n'
        xml += '    </' + method + '>\n'
        xml += '''  </soap:Body>
</soap:Envelope>
'''
        return xml

    def __check_connect(self):
        if self.available == 0:
            try:
                r = requests.get('http://' + self.path + '/WebService/ServiceV3.asmx?WSDL', headers={'Content-Type': 'application/x-www-form-urlencoded'})
                text = r.text
                if text.find('LoginListeningResponse') != -1:
                    self.available = 1
            except:
                library.fail('fail to connect server: ' + self.path)
                exit()
        return

    def __sopa_post(self, method, body):
        head = {'Username': self.username, 'Password': self.password}
        self.__encode_object(head)

        headers = {'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': 'http://www.open.com.cn/' + method}
        payload = self.__xml(method, head, body)

        r = requests.post('http://' + self.path + '/WebService/ServiceV3.asmx', headers=headers, data=payload)
        root = ET.fromstring(r.text)
        result = {}
        body = root[0][0]
        for child in body:
            if child.text != None:
                result[child.tag[24:]] = child.text
        return result

    def LoginListening(self):
        self.__check_connect()
        data = {'UserName': self.username, 'Password': self.password, 'Version': '4.0', 'LevelID': self.level}
        self.__encode_object(data)

        result = self.__sopa_post('LoginListening', data)

        self.__decode_object(result)
        result['ReturnMessage'] = result['ReturnMessage'].decode('gbk')

        try:
            self.UserID = result['UserID']
            self.UserNumber = result['UserNumber']
        except:
            pass
        return result

    def GetListeningProgress(self):
        self.__check_connect()
        data = {}
        data['UserID'] = self.UserID
        data['LevelID'] = self.level

        result = self.__sopa_post('GetListeningProgress', data)

        try:
            self.UnitID = result['UnitID']
        except:
            self.UnitID = '1'

        try:
            self.SectionID = result['SectionID']
        except:
            self.SectionID = self.level + self.UnitID + '11'
        return result

    def SetListeningUnitLearnStaus(self, status):
        self.__check_connect()
        data = {}
        data['UserID'] = self.UserID
        data['LevelID'] = self.level
        data['UnitID'] = self.UnitID
        data['Status'] = status
        self.__encode_object(data)

        result = self.__sopa_post('SetListeningUnitLearnStaus', data)

        self.__decode_object(result)
        return result

    def GetServerTime(self):
        self.__check_connect()
        data = {}

        result = self.__sopa_post('GetServerTime', data)

        self.BeginTime = result['GetServerTimeResult']
        return result

    def SetListeningResponseInformation(self, Score, IsCompleted):
        self.__check_connect()
        data = {}
        data['UserID'] = self.UserID
        data['UserNumber'] = self.UserNumber
        data['SectionID'] = self.SectionID
        data['SubSectionID'] = '0'
        data['Response'] = ''
        data['Score'] = Score
        data['IsSaveResponse'] = '0'
        data['IsCompleted'] = IsCompleted
        data['BeginTime'] = self.BeginTime
        self.__encode_object(data)

        result = self.__sopa_post('SetListeningResponseInformation', data)

        self.__decode_object(result)
        return result

    def SetListeningUserActiveInfo(self, SerialNumber, LicenseNumber, ActivationCode):
        self.__check_connect()
        data = {};
        data['UserID'] = self.UserID
        data['LevelID'] = self.level
        data['SerialNumber'] = SerialNumber
        data['LicenseNumber'] = LicenseNumber
        data['ActivationCode'] = ActivationCode
        data['IsActive'] = '2'
        self.__encode_object(data)

        result = self.__sopa_post('SetListeningUserActiveInfo', data)

        self.__decode_object(result)
        result['ReturnMessage'] = result['ReturnMessage'].decode('gbk')
        return result

def active(learn, SerialNumber, LicenseNumber, ActivationCode):
    result = learn.LoginListening()
    status = result['LoginListeningResult']
    if status == '2':
        library.warning('user ' + learn.username + ' have been actived')
        return '1'
    elif status != '1':
        if result['ReturnMessage'].find('Activation') == -1:
            library.fail('user ' + learn.username + ' login failed: ' + result['ReturnMessage'])
            exit()

    result = learn.SetListeningUserActiveInfo(SerialNumber, LicenseNumber, ActivationCode)
    status = result['SetListeningUserActiveInfoResult']
    if status == '1':
        library.success('user ' + learn.username + ' active successfully')
    else:
        library.fail('user ' + learn.username + ' active failed: ' + result['ReturnMessage'])
        exit()
    return status

def login(learn):
    result = learn.LoginListening()
    status = result['LoginListeningResult']
    if status == '1':
        library.warning('user ' + learn.username + ' need activation')
        exit()
    elif status != '2':
        library.fail('user ' + learn.username + ' login failed: ' + result['ReturnMessage'])
        exit()
    else:
        library.success('user ' + learn.username + ' login successfully')
    return status

def get_progress(learn):
    result = learn.GetListeningProgress()
    status = result['GetListeningProgressResult']
    return status

def update_unit(learn):
    result = learn.SetListeningUnitLearnStaus('1')
    status = result['SetListeningUnitLearnStausResult']
    if status == '1':
        library.success('update unit learn status success: unit '+ learn.UnitID)
    else:
        library.fail('update unit learn status fail: unit ' + learn.UnitID)
        exit()
    return status

def end_section(learn, score):
    result = learn.SetListeningResponseInformation("%.1f" % score, '1')
    status = result['SetListeningResponseInformationResult']
    if status == '1':
        library.success('ended section ' + learn.SectionID + ' successfully: score ' + "%.1f" % score)
    else:
        library.fail('ended section ' + learn.SectionID + ' failed')
        # Retry login
        status = login(learn)
        # Retry set response
        result = learn.SetListeningResponseInformation("%.1f" % score, '1')
        status = result['SetListeningResponseInformationResult']
        if status == '1':
            library.success('ended section ' + learn.SectionID + ' successfully: score ' + "%.1f" % score)
        else:
            library.fail('ended section ' + learn.SectionID + ' failed twice')
            exit()
    return status

def start_section(learn):
    result = learn.SetListeningResponseInformation('0', '0')
    status = result['SetListeningResponseInformationResult']
    if status == '1':
        library.success('started section ' + learn.SectionID + ' successfully')
    else:
        library.fail('started section ' + learn.SectionID + ' failed')
        exit()
    return status

var = {}

#use argparse to read command line
parser = argparse.ArgumentParser(description='A small, cross-platform program for NEIE.')
parser.add_argument('-s', '--path', type=str, help='path to server, may contain ip and port')
parser.add_argument('-u', '--username', type=str, help='username to login')
parser.add_argument('-p', '--password', type=str, help='password to login')
parser.add_argument('-l', '--level', type=str, help='current level')

parser.add_argument('-ac', '--activation', help='try to active user first', action='store_true')

parser.add_argument('-nf', '--no-file', help='stop read and write information to config.json', action='store_true')

parser.add_argument('--end-unit', help='stop at a unit before all unit learned')

parser.add_argument('--min-time',type=int, default=60 , help='min time to learn a unit, default 60')
parser.add_argument('--max-time',type=int, default=120, help='max time to learn a unit, default 120')
parser.add_argument('--min-mark',type=int, default=80 , help='min mark to learn a unit, default 80')
parser.add_argument('--max-mark',type=int, default=100, help='max mark to learn a unit, default 100')
args = parser.parse_args()

var['path'] = args.path
var['username'] = args.username
var['password'] = args.password
var['level'] = args.level

var['end-unit'] = args.end_unit

var['min-time'] = args.min_time
var['max-time'] = args.max_time
var['min-mark'] = args.min_mark
var['max-mark'] = args.max_mark

# sync information with config.json
if args.no_file == False:
    config_file = os.getcwd() + '/config.json'
    if os.path.isfile(config_file) == False:
        with open(config_file, 'w+') as f:
            pass
    with open(config_file, 'r+') as f:
        try:
            obj = json.load(f)
        except:
            obj = {}
        def sync(var, obj, names):
            for name in names:
                try:
                    obj[name]
                except:
                    obj[name] = None
                if var[name] == None:
                    var[name] = obj[name]
                elif var[name] != obj[name]:
                    obj[name] = var[name]
        sync(var, obj, [name for name in var])
        f.seek(0)
        json.dump(obj, f)

# check necessary arguments
if var['path'] == None or var['username'] == None or var['password'] == None or var['level'] == None:
    library.fail('missing required var')
    exit()

# Var init
learn = learn_english(var['path'], var['username'], var['password'], var['level']);

# Activation
if args.activation == True:
    print 'Get Activation Code at http://www.neie.edu.cn/License/LicenseActivation.aspx'
    SerialNumber = raw_input('Serial Number: ')
    LicenseNumber = raw_input('License Number: ')
    ActivationCode = raw_input('Activation Code: ')

    print 'Confirm your information'
    print 'Path: ' + var['path']
    print 'Username: ' + var['username']
    print 'Level: ' + var['level']
    print 'Serial Number: ' + SerialNumber
    print 'License Number: ' + LicenseNumber
    print 'Activation Code: ' + ActivationCode

    answer = raw_input('Is above information all right? (y/n)')
    if answer == 'Y' or answer == 'y':
        SerialNumber = SerialNumber.replace(' ', '').replace('-', '')
        LicenseNumber = LicenseNumber.replace(' ', '').replace('-', '')
        ActivationCode = ActivationCode.replace(' ', '').replace('-', '')
        active(learn, SerialNumber, LicenseNumber, ActivationCode)
    else:
        exit()

# Login
if args.activation == False:
    status = login(learn)

# Get Progress
status = get_progress(learn)
if status == '1':
    fetch = library.fetch(learn.level, learn.SectionID)
    if fetch['next']['unit'] != learn.UnitID:
        update_unit(learn, fetch)
        learn.UnitID = fetch['next']['unit']
        learn.SectionID = fetch['next']['section']

# Learn English
while True:
    learn.GetServerTime()
    library.success('learning english: unit ' + learn.UnitID + ', section ' + learn.SectionID)
    library.timer(random.randint(var['min-time'], var['max-time']))
    library.success('finished learning: unit ' + learn.UnitID + ', section ' + learn.SectionID)

    fetch = library.fetch(learn.level, learn.SectionID)
    if fetch['problem'] == 0:
        score = 0
    else:
        # Get int in next two var
        min_problem = var['min-mark'] * fetch['problem'] / 100 + 1
        max_problem = var['max-mark'] * fetch['problem'] / 100
        if min_problem > max_problem:
            min_problem = max_problem
        score = random.randint(min_problem, max_problem) * 100.0 / fetch['problem']
    status = end_section(learn, score)

    try:
        fetch['next']
    except:
        # end of all section
        status = update_unit(learn)
        break;

    if fetch['next']['unit'] != learn.UnitID:
        status = update_unit(learn)
        if learn.UnitID == var['end-unit']:
            break
        learn.UnitID = fetch['next']['unit']
    learn.SectionID = fetch['next']['section']

    status = start_section(learn)
