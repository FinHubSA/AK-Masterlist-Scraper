from itertools import count
import time
import random
import os.path
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import sys
import urllib
import pydub
import speech_recognition as sr
from selenium.webdriver.common.keys import Keys
from selenium import webdriver

class recaptcha_solver:

    def __init__(self, driver: webdriver):

        self._driver = driver

        def delay(waiting_time=random.randrange(5,30,1)):
            driver.implicitly_wait(waiting_time)
        
        count=0
        while True:
            count=count+1
            print(count)
            try:
                WebDriverWait(driver,30).until(expected_conditions.presence_of_element_located((By.XPATH, r"//div/iframe")))
                frames = driver.find_elements(By.TAG_NAME,"iframe")

                recaptcha_control_frame = None
                recaptcha_challenge_frame = None

                for index,frame in enumerate(frames):
                    # Find the reCAPTCHA checkbox
                    if re.search('reCAPTCHA', frame.get_attribute("title")):
                        recaptcha_control_frame = frame
                        print('recaptcha box located')
                    # Find the reCAPTCHA puzzle    
                    if re.search('recaptcha challenge expires in two minutes', frame.get_attribute("title")):
                        recaptcha_challenge_frame = frame
                        print('recaptcha puzzle located')
                if not (recaptcha_control_frame or recaptcha_challenge_frame):
                    print("[ERR] Unable to find recaptcha.")
                
                # switch to checkbox
                delay()
                frames = driver.find_elements(By.TAG_NAME,"iframe")
                driver.switch_to.frame(recaptcha_control_frame)

                # click on checkbox to activate recaptcha
                driver.find_element(By.CLASS_NAME,"recaptcha-checkbox-border").click()

                print("checkbox clicked")

                time.sleep(10)
            
            except:
                print("An error has occured.")
                print("IP address might have been blocked for recaptcha.")
                break
  
            try:
                print("trying to find JSTOR page")               
                WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.XPATH, r"//div[@data-qa='stable-url']")))
                print("ReCAPTCHA successfully solved after the checkbox was clicked")
                count_puzzle_solver=False
                break
            except:      
                try:
                    # switch to recaptcha audio control frame
                    delay()
                    driver.switch_to.default_content()
                    frames = driver.find_elements(By.TAG_NAME,"iframe")
                    driver.switch_to.frame(recaptcha_challenge_frame)

                    # click on audio challenge
                    time.sleep(10)
                    driver.find_element(By.ID,"recaptcha-audio-button").click()
                    print("Switched to audio control frame")
                    
                    count_puzzle_solver=True
                    break
                except:
                    print("recurring checkbox")
                    if count >= random.randrange(3,6,1):
                        delay()
                        driver.get(driver.current_url)
                        count=0
                        delay()
                        driver.navigate().refresh()
                    continue
        
        while count_puzzle_solver:
            # switch to recaptcha audio challenge frame
            driver.switch_to.default_content()
            frames = driver.find_elements(By.TAG_NAME,"iframe")
            driver.switch_to.frame(recaptcha_challenge_frame)

            # get the mp3 audio file
            delay()
            src = driver.find_element(By.ID,"audio-source").get_attribute("src")
            print(f"[INFO] Audio src: {src}")

            path_to_mp3 = os.path.normpath(os.path.join(os.getcwd(), "sample.mp3"))
            path_to_wav = os.path.normpath(os.path.join(os.getcwd(), "sample.wav"))

            # download the mp3 audio file from the source
            urllib.request.urlretrieve(src, path_to_mp3)

            # load downloaded mp3 audio file as .wav
            try:
                sound = pydub.AudioSegment.from_mp3(path_to_mp3)
                sound.export(path_to_wav, format="wav")
                sample_audio = sr.AudioFile(path_to_wav)
                print("Exported audio file to .wav")
            except Exception:
                print(
                    "[ERR] Please run program as administrator or download ffmpeg manually, "
                    "https://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/"
                    )

            # translate audio to text with google voice recognition
            delay()
            r = sr.Recognizer()
            with sample_audio as source:
                audio = r.record(source)
                try:
                    key = r.recognize_google(audio)
                    print(f"[INFO] Recaptcha Passcode: {key}")
                    print("Audio Snippet was recognised")
                except:
                    print("reCAPTCHA voice segment is too difficult to solve.")
                    break

            # key in results and submit
            delay()
            try:
                driver.find_element(By.ID,"audio-response").send_keys(key.lower())
                driver.find_element(By.ID,"audio-response").send_keys(Keys.ENTER)
                time.sleep(5)
                driver.switch_to.default_content()
                time.sleep(5)
                print("Audio snippet submitted")
            except:
                print("An error has occured.")
                print("IP address might have been blocked for recaptcha.")
                break

            while True:
                try:
                    # check to see if reCAPTCHA was solved
                    print("trying to find JSTOR page")
                    WebDriverWait(driver,10).until(expected_conditions.presence_of_element_located((By.XPATH, r"//div[@data-qa='stable-url']")))
                    print("ReCAPTCHA successfully solved")
                    count_puzzle_solver=False
                    break
                except:
                    try:
                        # check to see if checkbox pops up
                        print("trying to find and solve checkbox")
                        driver.get(driver.current_url)
                        print("refreshed page")
                        delay()

                        WebDriverWait(driver,30).until(expected_conditions.presence_of_element_located((By.XPATH, r"//div/iframe")))
                        frames = driver.find_elements(By.TAG_NAME,"iframe")

                        recaptcha_control_frame = None
                        recaptcha_challenge_frame = None

                        for index,frame in enumerate(frames):
                            # Find the reCAPTCHA checkbox
                            if re.search('reCAPTCHA', frame.get_attribute("title")):
                                recaptcha_control_frame = frame
                                print('recaptcha box located')
                            # Find the reCAPTCHA puzzle    
                            if re.search('recaptcha challenge expires in two minutes', frame.get_attribute("title")):
                                recaptcha_challenge_frame = frame
                                print('recaptcha puzzle located')
                        if not (recaptcha_control_frame or recaptcha_challenge_frame):
                            print("[ERR] Unable to find recaptcha.")
                        
                        # switch to checkbox
                        delay()
                        frames = driver.find_elements(By.TAG_NAME,"iframe")
                        driver.switch_to.frame(recaptcha_control_frame)

                        # click on checkbox to activate recaptcha
                        driver.find_element(By.CLASS_NAME,"recaptcha-checkbox-border").click()

                        print("checkbox clicked")
                        delay()
                    except:
                        print("Trying to solve reCAPTCHA puzzle")
                        break

        

           