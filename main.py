from classes.gen import adidas
import json, colorama, threading
from classes.logger import logger

colorama.init()
log = logger().log

numThread = 1

log("--------------------------", "gray")
log("Confirmed Account Gen", "yellow")
log("By: Euphoria & Zruss", "yellow")
log("--------------------------", "gray")



try:
    with open('./config/proxies.json') as json_data_file:
        proxies = json.load(json_data_file)
        log("%s Proxy(s) Loaded" % len(proxies), "info")
except:
    log("Error in proxy file..", "error")
    quit()

try:
    with open('./config/config.json') as json_data_file:
        config = json.load(json_data_file)
        log("Config Loaded", "info")
except:
    log("Error in config.json...", "error")
    quit()
log("--------------------------", "gray")



def main(x, proxies, config):
    AC = adidas(x, proxies, config)
    AC.run()


threads = []
log("Starting Tasks...", "clear")
for x in range(config['numofAccounts']):
    t = threading.Thread(target= main, args=(x, proxies, config))
    threads.append(t)
    t.start()