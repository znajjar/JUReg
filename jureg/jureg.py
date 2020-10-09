from datetime import datetime
import platform
import threading
import time
from collections import Iterable
from io import BytesIO

from .errors import *
from .data import Data

from PIL import Image
from PIL import ImageFilter
import pytesseract

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select


class JUReg:
    """
    Main class. Creates an instance of firefox webdriver and goes to the JU registration website

    Parameters
    -----------
    username: :class:`str`
        The username of the account you want to access the website with.
    password: :class:`str`
        The password of the account you want to access the website with.
    filepath: :class:`str`
        Alternatively sign-in credentials can be provided in a file as demonstrated in the example.
    target: :class:`Callable`
        Callback function after checking courses is finished. Expects a dictionary of open courses found with
        the course ID as the key and a list of open sections of that course as the value.
    ocr: :class:`Callable`
        This gives the option to provide an alternative OCR function. The built-in function is 70% accurate
        but better results could be achieved. Expects a PIL Image and returns a str of the captcha word.
    headless: :class:`bool`
        This gives the option to make the webdriver headless. If set to True the constructor won't launch the webdriver
        GUI and everything will be ran in the background.
    refresh: :class:`int`
        How often you want the watched courses to be checked in minutes. If set to -1 it will only
        perform a single check.
    driver: :class:`str`
        The browser you want to use. 'ff' for Firefox, 'ch' for Chrome.
    """
    tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    _reg_url = 'https://regweb1.ju.edu.jo:4443/selfregapp/home.xhtml'
    _schedule_url = 'https://regweb1.ju.edu.jo:4443/selfregapp/secured/ofrd-course.xhtml'
    _DELAY = 0.05
    _ATTEMPTS = 5
    _DELAY_FACTOR = 1.5
    _DELAY_MIN = 0

    def __init__(self, username=None, password=None, filepath=None, target=None, ocr=None,
                 headless=False, refresh=5, driver='ff'):
        self._username = None
        self._password = None
        if username is not None and password is not None:
            self._password = password
            self._username = username
        elif filepath is not None:
            with open(filepath) as credentials:
                self._username = credentials.readline()
                self._password = credentials.readline()

        self.target = target
        options = Options() if driver == 'ff' else webdriver.ChromeOptions()
        if headless: options.add_argument("--headless")
        if driver == 'ff':
            self._driver = webdriver.Firefox(options=options)
        elif driver == 'ch':
            self._DELAY_MIN = 0.5
            self._driver = webdriver.Chrome(options=options)
        else:
            raise WrongDriverArgument
        self._get(self._reg_url)
        self._ocr = ocr
        if self._ocr is None: self._ocr = self._get_captcha

        self._refresh = refresh
        self._faculties = Data.data
        self._watching = {}
        self._found = {}
        self._running = False
        self._running_thread = None
        if platform.system() == 'Windows':
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

    def set_username(self, username):
        if not isinstance(username, str):
            raise TypeError
        self._username = username

    def set_password(self, password):
        if not isinstance(password, str):
            raise TypeError
        self._password = password

    def set_credentials(self, username, password):
        self.set_username(username)
        self.set_password(password)

    def set_refresh(self, refresh):
        self._refresh = refresh

    def add_sections(self, courseID: str, sections):
        # Splits the ID into three segments. Same way they are divided into categories on the website
        facultyID = courseID[0:2]
        departmentID = courseID[2:4]
        courseID = courseID[4:]

        if facultyID not in self._watching: self._watching[facultyID] = {}
        faculty = self._watching[facultyID]

        if departmentID not in faculty: faculty[departmentID] = {}
        dep = faculty[departmentID]

        if courseID not in dep: dep[courseID] = set()
        course = dep[courseID]

        if isinstance(sections, Iterable):
            for sec in sections: course.add(int(sec))
        elif isinstance(sections, int):
            course.add(sections)
        elif isinstance(sections, str):
            sections = sections.split()
            for sec in sections: course.add(int(sec))
        else:
            raise TypeError

    def run(self):
        # Starts a new thread so it doesn't block the flow of the program.
        self._running_thread = threading.Thread(target=self._run)
        self._running_thread.start()

    def check_watching(self):
        # Checks for the watched list and returns a map of open courses. Doesn't call the target function. Note that
        # calling this function will block your program until it finishes checking
        self._login()
        self._found = {}
        self._get(self._schedule_url)

        degrees = self._driver.find_element_by_class_name('selectonemenu')
        degrees = Select(degrees)
        degrees.select_by_index(1)

        time.sleep(self._DELAY)
        facultySelector = Select(self._driver.find_elements_by_class_name('selectonemenu')[1])

        for fac in self._watching:
            facIdx, depsIDs = self._faculties[fac]
            facultySelector.select_by_index(facIdx)

            time.sleep(self._DELAY)
            depsSelector = Select(self._driver.find_elements_by_class_name('selectonemenu')[2])

            for dep in self._watching[fac]:
                depIdx = depsIDs[dep]
                depsSelector.select_by_index(depIdx)

                try:
                    pages = WebDriverWait(self._driver, timeout=self._DELAY * 2).until(
                        expected_conditions.presence_of_element_located((By.CLASS_NAME, 'ui-paginator-top')))
                except TimeoutException:
                    pages = None

                if pages is None:
                    self._find_sections(fac + dep, self._watching[fac][dep])
                else:
                    pagesCount = len(pages.find_elements_by_class_name('ui-paginator-page'))
                    for pageIdx in range(pagesCount):
                        pages = self._driver.find_element_by_class_name('ui-paginator-top')
                        pages.find_elements_by_class_name('ui-paginator-page')[pageIdx].click()
                        self._find_sections(fac + dep, self._watching[fac][dep])
        self._get(self._reg_url)
        return self._found

    def _get(self, url):
        current_time = datetime.now()
        self._driver.get(url)
        self._DELAY = min((datetime.now() - current_time).total_seconds() * self._DELAY_FACTOR + self._DELAY_MIN, 10)

    def _run(self):
        while True:
            while self._running: pass
            self._running = True
            for attempt in range(1, self._ATTEMPTS + 1):
                try:
                    self.check_watching()
                    break
                except StaleElementReferenceException as e:
                    if attempt == self._ATTEMPTS + 1: raise e
                    print(e)
                except NoSuchElementException as e:
                    if attempt == self._ATTEMPTS + 1: raise e
                    print(e)
                finally:
                    self._DELAY_FACTOR += 0.5
            else:
                raise CouldNotFinishOperation

            self.target(self._found)
            if self._refresh == -1: break
            self._running = False
            time.sleep(self._refresh * 60)
        self._running = False

    def _find_sections(self, departmentID, courses):
        time.sleep(self._DELAY)
        for course in courses:
            courseID = departmentID + course
            sections = courses[course]
            occurrences = self._driver.find_elements_by_xpath("//*[contains(text(), '{}')]".format(courseID))
            for occ in occurrences:
                occ = occ.find_element_by_xpath("..")
                cells = occ.find_elements_by_xpath(".//*")
                if cells[12].text == 'Opened' and int(cells[3].text) in sections:
                    if courseID not in self._found: self._found[courseID] = []
                    self._found[courseID].append(int(cells[3].text))

    def _login(self):
        # keeps trying until it gets the captcha correct
        while True:
            self._checkEng()
            self._get(self._reg_url)

            try:
                captcha = self._driver.find_element_by_id('loginform:imgCaptchaId').screenshot_as_png
            except NoSuchElementException:
                # if captcha isn't found then it's already logged in
                return

            captcha_img = Image.open(BytesIO(captcha))
            captchaText = self._ocr(captcha_img)

            if self._username is None or self._password is None:
                raise CredentialsNotProvided

            self._driver.find_elements_by_class_name('ui-inputfield')[0].send_keys(self._username)
            self._driver.find_elements_by_class_name('ui-inputfield')[1].send_keys(self._password)
            self._driver.find_elements_by_class_name('ui-inputfield')[2].send_keys(captchaText)

            self._driver.find_elements_by_class_name('ui-button')[0].click()

    def _checkEng(self):
        # Makes sure the website is in english before logging in.
        try:
            button = self._driver.find_element_by_xpath("//*[contains(text(), 'English')]")
        except NoSuchElementException:
            return

        button.click()

    @staticmethod
    def _get_captcha(captcha_img):
        # Transforming image
        captcha_img = captcha_img.rotate(11, Image.BICUBIC)
        captcha_img = captcha_img.crop((2, 15, captcha_img.size[0] - 25, captcha_img.size[1] - 5))
        captcha_img = captcha_img.resize((captcha_img.size[0] * 2, captcha_img.size[1] * 2))
        # Applying filters (MedianFilter removes noise)
        captcha_img = captcha_img.filter(ImageFilter.EDGE_ENHANCE)
        captcha_img = captcha_img.filter(ImageFilter.MedianFilter)
        captcha_img = captcha_img.filter(ImageFilter.MedianFilter)
        captcha_img = captcha_img.filter(ImageFilter.SMOOTH_MORE)

        custom_config = r'--oem 3 --psm 7 min_characters_to_try 5' \
                        r'load_system_dawg false' \
                        r'load_freq_dawg false' \
                        r'tessedit_char_whitelist abcdefghijklmnopqrstuvwxyz0123456789'

        return pytesseract.image_to_string(captcha_img, config=custom_config).splitlines()[0]
