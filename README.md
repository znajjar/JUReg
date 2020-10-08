JUReg
===

A web scraper for the [registration website](https://regweb1.ju.edu.jo:4443/selfregapp/home.xhtml) of the University of Jordan.

![reg_site_image](https://user-images.githubusercontent.com/42502239/95434861-73d55700-095a-11eb-9445-cf83c6ebbd55.png)

This library accesses the registration website and looks for courses you want to register in and tells you if any of them is open saving you a lot of time and effort.

Installation
===
Place the jureg folder in under (..\Python\Lib\site-packages). This will install the library system-wide.  
Alternatively, you can just place it in the same directory as your python script.

### Dependencies: 
* `PIL` - pip install Pillow
* `pytesseract` - pip install pytesseract  
You need to download [tesseract](https://github.com/tesseract-ocr/tesseract) and place it under (C:\Program Files\) on windows.  
If you're on another OS you'll have to fix the directory in the source code.

* `selenium` - pip install selenium  
You also have to download [geckodriver](https://github.com/mozilla/geckodriver/releases) and put it in PATH.

Usage
===
**Constructor**  
Parameters:
* `username`: The username of the account you want to access the website with.
* `password`: The password of the account you want to access the website with.  
* `filepath`: Alternatively sign-in credentials can be provided in a file as demonstrated in the example.
* `target`: Callback function after checking courses is finished. Expects a dictionary of open courses found with
        the course ID as the key and a list of open sections of that course as the value.
* `ocr`: This gives the option to provide an alternative OCR function. The built-in function is 70% accurate
        but better results could be achieved. Expects a PIL Image and returns a str of the captcha word.
* `headless`: This gives the option to make the webdriver headless. If set to True the constructor won't launch the webdriver
        GUI and everything will be ran in the background.
* `refresh`: How often you want the watched courses to be checked in minutes. If set to -1 it will only
        perform a single check.  

**add_sections()**  
Parameters:
* `courseID`: The ID of the course the sections belong to.
* `sections`: List of sections you want `JUReg` to watch for you.

example:  
Let's say you want to it to keep checking these sections:  
![sections_image](https://user-images.githubusercontent.com/42502239/95435251-05dd5f80-095b-11eb-9c55-5a1f16b0affd.png)  
you do the following: 
```python
JU.add_sections('0907528', [1, 2])
```
**run()**  
Calling this starts a new thread and keeps calling `check_watching()` every `refresh` minutes and calls `target` after it's done checking.  

**check_watching()**  
Calling this will only check watched courses once and return the results in a dictionary.
