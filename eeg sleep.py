from ast import arg
from audioop import add
from datetime import datetime
from lib2to3.pgen2.token import EQUAL
from time import sleep
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import operator
import datetime
import csv  

#Network Variables
ip = "0.0.0.0"
port = 5000

#Muse Variables
hsi = [4,4,4,4]
hsi_string = ""
abs_waves = [-1,-1,-1,-1,-1]
rel_waves = [-1,-1,-1,-1,-1]


gamma=0
beta=0
alpha=0
theta=0
delta=0
passCounter=0

timesDeepSleep=0
alreadyDeepSleepd=False

mov_history=0
moved=False

max_t=60


def hsi_handler(address: str,*args):
    global hsi, hsi_string
    hsi = args
    if ((args[0]+args[1]+args[2]+args[3])==4):
        hsi_string_new = "Muse Fit Good"
    else:
        hsi_string_new = "Muse Fit Bad on: "
        if args[0]!=1:
            hsi_string_new += "Left Ear. "
        if args[1]!=1:
            hsi_string_new += "Left Forehead. "
        if args[2]!=1:
            hsi_string_new += "Right Forehead. "
        if args[3]!=1:
            hsi_string_new += "Right Ear."        
    if hsi_string!=hsi_string_new:
        hsi_string = hsi_string_new
        # print(hsi_string)  

def gyro_handler(address: str,*args):
    global mov_history,moved
    current=(args[0]+args[1]+args[2])
    if(int(current-mov_history)!=0):
        moved=True
    mov_history=current


def show_data():
    global gamma,beta,alpha,theta,delta,t,max_t,moved,passCounter,alreadyDeepSleepd

    while True:
        sleep(max_t)
        if(gamma!=0 and beta!=0 and alpha!=0 and theta!=0 and delta!=0):
            thisdict = {
                "GAMMA": gamma/passCounter,
                "BETA":beta/passCounter,
                "ALPHA":alpha/passCounter,
                "THETA":theta/passCounter,
                "DELTA":delta/passCounter
            }

            keys_list = list(dict( sorted(thisdict.items(), key=operator.itemgetter(1),reverse=True)))
            wave=str(keys_list[0])
            data="";

            if wave == "DELTA":  # se esta em DELTA
                if not moved:    # se não houve movimentos fisicos, então realmente esta em sono profundo
                    if not alreadyDeepSleepd: # se ja nao esteve em sono profundo antes (para facilitar a detectção do sono REM)
                        if timesDeepSleep<5:  # se ainda nao teve 5 minutos seguidos de sono profundo
                            timesDeepSleep=timesDeepSleep+1 # adiciona +1 minuto para no contador para certificar sono profundo
                            data="Provavelmente em sono profundo"
                        else:                 # caso ja tenha passado de 5 minitos de sono profundo)
                            data="Em sono profundo"
                            alreadyDeepSleepd=True # guarda o valor de realmente ja ter passado mais de 5 minutos de sono profundo  
                    else: # ja esteve em sono profundo antes
                        if timesDeepSleep<5:  # se ainda nao teve 5 minutos seguidos de sono profundo
                            timesDeepSleep=timesDeepSleep+1 # adiciona +1 minuto para no contador para certificar sono profundo
                            data="Provavelmente em sono profundo"
                        else:                 # caso ja tenha passado de 5 minitos de sono profundo)
                            data="Em sono profundo"
                            alreadyDeepSleepd=True # guarda o valor de realmente ja ter passado mais de 5 minutos de sono profundo  
                else:  
                    data="Acordado" # esta em delta porem houve movimentos entao é um falso sono profundo
                    if not alreadyDeepSleepd: # se ja nao esteve em sono profundo antes (para facilitar a detectção do sono REM)
                        timesDeepSleep=0 # reinicializa o contador de minutos seguidos de sono profundo   
                    
            else: # se tem actividade cerebral e NAO esta em sono profundo
                timesDeepSleep=0 # reinicializa o contador de minutos seguidos de sono profundo   
                if alreadyDeepSleepd: # Ja esteve em sono profundo antes
                    data="Provavelmente a sonhar"
                else:
                    data="Acordado"

            now = datetime.datetime.now()
            print(str(now.hour)+":"+str(now.minute)+":"+str(now.second)+" = "+data)

            fields=[str(now.hour)+":"+str(now.minute)+":"+str(now.second),data]
            with open(r'EEG_SLEEP_LOG.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(fields)
            moved=False
            gamma=0
            beta=0
            alpha=0
            theta=0
            delta=0
            passCounter=0

def abs_handler(address: str,*args):
    global hsi, abs_waves, rel_waves,hsi_ok,passCounter
    global gamma,beta,alpha,theta,delta
    wave = args[0][0]
    
    sumVals=0
    countVals=0            
    for i in [0,1,2,3]:
        if hsi[i]==1: #Only use good sensors
            countVals+=1
            sumVals+=args[i+1]
    if(countVals>0):
        abs_waves[wave] = sumVals/countVals
        passCounter=passCounter+1

    if(address.find("gamma")!=-1):
        gamma+=abs_waves[wave]
    if(address.find("beta")!=-1):
        beta+=abs_waves[wave]
    if(address.find("alpha")!=-1):
        alpha+=abs_waves[wave]
    if(address.find("theta")!=-1):
        theta+=abs_waves[wave]
    if(address.find("delta")!=-1):
        delta+=abs_waves[wave]


    
if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/elements/delta_absolute", abs_handler,0)
    dispatcher.map("/muse/elements/theta_absolute", abs_handler,1)
    dispatcher.map("/muse/elements/alpha_absolute", abs_handler,2)
    dispatcher.map("/muse/elements/beta_absolute", abs_handler,3)
    dispatcher.map("/muse/elements/gamma_absolute", abs_handler,4)

    dispatcher.map("/muse/gyro", gyro_handler)

    dispatcher.map("/muse/elements/horseshoe", hsi_handler)
    x = threading.Thread(target=show_data)
    x.daemon = True
    x.start()
    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print("Listening on UDP port "+str(port))
    server.serve_forever()
