import requests, time, random, colorama
from bs4 import BeautifulSoup as bs
from classes.logger import logger
from faker import Faker



class adidas():
    def __init__(self, x, proxies, config):
        colorama.init()
        self.log = logger().log
        self.s = requests.session()
        self.x = x
        self.faker = Faker()
        self.s.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.8,en;q=0.6",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
        }
        self.s.headers.update()
        self.proxies = proxies
        self.config = config
        self.catchall = self.config['accountInfo']['catchall']
        self.password = self.config['accountInfo']['password']
        self.apiKey = self.config['smspva']['apikey']


    
    def randproxy(self):
        if self.config['use_proxies']:
            self.proxy = random.choice(self.proxies)
            self.proxyDict = {
                'http': self.proxy,
                'https': self.proxy
            }
            self.s.proxies.update(self.proxyDict)
        else:
            pass
    
    def create(self):
        fname = self.faker.first_name()
        lname = self.faker.last_name()
        self.email = fname + lname + str(random.randint(100, 1000) * 2) + self.catchall
        dob   = str(random.randint(1970, 1996)) + "-" + str(random.randint(10, 12)) + "-" + str(random.randint(10, 30))


        if self.config['accountInfo']['region'] == "US":
            self.region = "US"
            self.vid    = "US"
            self.tokenURL = "https://cp.adidas.com/as/token.oauth2"
        elif self.config['accountInfo']['region'] == "UK":
            self.region = "GB"
            self.vid    = "DE" 
            self.tokenURL = "https://cp.adidas.co.uk/as/token.oauth2"
        elif self.config['accountInfo']['region'] == "CA":
            self.region = "CA"

        data = {
            "clientId": "1ffec5bb4e72a74b23844f7a9cd52b3d",
            "actionType": "REGISTRATION",
            "email":  self.email,
            "password":  self.password,
            "countryOfSite": self.region,
            "dateOfBirth":  dob,
            "minAgeConfirmation": "Y",
            "firstName": fname,
            "lastName": lname
        }
        
        re = self.s.post("https://apim.scv.3stripes.net/scvRESTServices/account/createAccount", json=data)
        if "iCCD_CRT_ACCT_0001" in re.text:
            self.log("[%s] Account created with: " % self.x + self.email, "success")
        elif "Denied" in re.text:
            self.log("[%s] Banned.. Rotating Proxy... " % self.x, "error")
            time.sleep(5)
            self.randproxy()
            self.create()
            pass
        elif "Already_Email_Exists" in re.text:
            self.log("[%s] Email Already Used... " % self.x, "error")
            time.sleep(5)
            self.create()
            pass

    def token(self):   
        self.s.headers = {
            'Accept': 'application/json',
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.8,en;q=0.6",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        self.s.headers.update()

        authData = {
            "client_id"     : "1ffec5bb4e72a74b23844f7a9cd52b3d",
            "username"      : self.region + "|" + self.email,
            "password"      : self.password,
            "validator_id"  : "confirmed4oauth" + self.vid,
            "grant_type"    : "password",
            "scope"         : "pii mobile2web",
            "access_token_manager_id": "jwt"
        }
        auth = self.s.post(self.tokenURL, data=authData)
        if auth.status_code == 200:
            json = auth.json()
            self.accessToken = json['access_token']
            if self.config['debug']:
                self.log('[%s] Access Token: ' % self.x + str(self.accessToken[0:10]), "success")
        else:
            self.log('[%s] Error Grabbing token. (%s) ' % (self.x, auth.text), "error")
            time.sleep(5)
            self.token()

        lookUpdata = {
            "oauthToken": self.accessToken,
            "includePersonalInformation": "Y",
            "version": "12.0"
        }
        res = self.s.post("https://apim.scv.3stripes.net/scvRESTServices/account/lookUpAccount", json=lookUpdata)
        if res.status_code == 200:
            json = res.json()
            self.euci = json['euci']
            if self.config['debug']:
                self.log('[%s] Euci: ' % self.x + str(self.euci), "success")
        else:
            self.log('[%s] Error Grabbing Euci... (%s) ' % (self.x, res.text), "error")
            time.sleep(5)
            self.token()

        self.s.headers = {
            'Accept': 'application/json',
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.8,en;q=0.6",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
            "Content-Type": "application/json"
        }
        self.s.headers.update()
        

        usersData = {
                    "loginProvider": {
                        "type": "scv",
                        "data": {
                            "euci": self.euci,
                             "scvToken": self.accessToken
                        }
                    },
                    "country": self.region
                }
        users = self.s.post("https://api.adidas-confirmed.monkapps.com/api/v3/users", json=usersData)
        if users.status_code == 200:
            json = users.json()
            self.userID = json['data']['account']['id']
            if self.config['debug']:
                self.log('[%s] userID: ' % self.x + str(self.userID), "success")
        else:
            self.log('[%s] Error Grabbing User Data: ' % self.x + str(users.text), "error")
            time.sleep(5)
            quit()

         

    def getphone(self):
        getNumberURL = "http://smspva.com/priemnik.php?metod=get_number&country=UK&service=opt85&id=1&apikey=%s" % self.apiKey
        while True:
            re = self.s.get(getNumberURL).json()
            if re['response'] == "2":
                self.log('[%s] All Numbers Taken... ' % self.x, "info")
                time.sleep(5)
            elif re['response'] == "1":
                self.number = re['number']
                self.id     = re['id']
                self.log('[%s] PhoneNumber: ' % self.x + str(self.number), "success")
                break
            elif re['response'] != "2" or "1" :
                self.log('[%s]' % self.x + str(re), "error")
                time.sleep(10)

        
    def verify(self):
        data = {"isdCountry":"GB","phoneNumber":self.number}

        re = self.s.post("https://api.adidas-confirmed.monkapps.com/api/v3/validate/phone-number", json=data)
        if re.status_code == 200:
            pass
        else:
            json = re.json()
            msg  = json['error']['code']['message']
            self.log('[%s] %s' % (self.x, str(msg)), "error")


        codeData = {"phoneNumber":self.number,"euci":self.euci,"isdCountry":"GB"}

        re = self.s.post("https://api.adidas-confirmed.monkapps.com/api/v3/users/%s/verify/code" % self.userID, json=codeData)
        if re.status_code == 200:
            json = re.json()
            self.verifyID = json['data']['verifyId']
            if self.config['debug']:
                self.log('[%s] verifyID: ' % self.x + str(self.verifyID), "success")
        else:
            self.log('[%s]' % self.x + str(json), "error")



        
        getsmsUrl = "http://smspva.com/priemnik.php?metod=get_sms&country=UK&service=opt85&id=%s&apikey=%s" % (self.id, self.apiKey)
        while True:
            re = self.s.get(getsmsUrl).json()
            if re['response'] == "2":
                self.log('[%s] No SMS Yet... ' % self.x, "info")
                time.sleep(5)
            elif re['response'] == "1":
                self.smscode = re['sms']
                self.log('[%s] SMS CODE: ' % self.x + str(self.smscode), "success")
                break
            else:
                self.log('[%s]' % self.x + str(re), "error")
                time.sleep(5)

        installURL = "https://api.adidas-confirmed.monkapps.com/api/v1/app/install"
        re = self.s.post(installURL, data=None)
        if re.status_code == 200:
            json = re.json()
            self.installToken = json['data']['installationToken']
            if self.config['debug']:
                self.log('[%s] Install Token: ' % self.x + str(self.installToken[0:15]), "success")
        else:
            self.log('[%s] Error Grabbing Install Token.. Retrying...' % self.x, "error")
            time.sleep(5)
            self.verify()


        verifyData = {"installationToken":self.installToken,"verifyId":self.verifyID,"code":self.smscode}
        re = self.s.post("https://api.adidas-confirmed.monkapps.com/api/v3.1/users/%s/verify" % self.userID, json=verifyData)
        if re.status_code == 200:
            self.log("[%s] Account Verified!" % self.x, "success")
        else:
            self.log('[%s] Failed to verify account' % self.x, "error")
            self.log('[%s] %s' % (self.x, re.text))


        data = {"isdCountry":"GB","phoneNumber":"0" + self.number}
        re = self.s.post("https://api.adidas-confirmed.monkapps.com/api/v3/validate/phone-number", json=data)
        if re.status_code == 200:
            pass
        else:
            json = re.json()
            msg  = json['error']['code']['message']
            self.log('[%s] %s' % (self.x, str(msg)), "error")

        
        updateData = {
            "oauthToken": self.accessToken,
            "countryOfSite":self.region ,
            "actionType": "UPDATEPROFILE",
            "consumerAttributes": {
                "consumerAttribute": [{
                    "attributeName": "CONFIRMED_PHONENUMBER",
                    "attributeValue": "0044" + self.number
                    }, {
                    "attributeName": "HYPE_SIGNUP",
                    "attributeValue": "Y"
                    }]
                }
            }
        update = self.s.post("https://apim.scv.3stripes.net/scvRESTServices/account/updateAccount", json=updateData).json()
        if update['conditionCode'] == "iCCD_UPDT_ACCT_0001":
            self.log('[%s] Account Updated & Finished!' % self.x, "success")
            with open("./config/accounts.txt", "a") as f:
                f.write(self.email + ":" + self.password + "\n")
                f.close()
        else:
            self.log('[%s] Error Finishing account!' % self.x, "error")



        banURL   = "http://smspva.com/priemnik.php?metod=ban&service=opt85&apikey=%s&id=%s" % (self.apiKey, self.id)
        while True:
            re = self.s.get(banURL).json()
            if re['response'] == "1":
                self.log('[%s] Number Succesfully Banned' % self.x, "success")
                break
            else:
                self.log('[%s]' % self.x + str(re), "error")
                time.sleep(30)






    
    def run(self):
        self.randproxy()
        self.create()
        self.token()
        self.getphone()
        self.verify()



    


