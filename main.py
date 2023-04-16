from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.service import Service
import re

"""
konfigurointi:
- TE-palvelut (https://paikat.te-palvelut.fi/tpt/)
- url muuttujaan laitetaan haun aloitusnäkymä. Valitse itse haettavat ammattiryhmät tai hae
sanahaulla ja paina näytä ilmoitukset. Sen jälkeen kopioi url tänne muuttujaan.
- max_sample_size on tarkasteltavien ilmoitusten maksimimäärä. Ilmoitusten lataus
(luultavasti) alkaa listan alusta ja jatkuu järjestyksessä siitä.
- driver_location on chromedriverin sijainti. (asenna se) (https://chromedriver.chromium.org/)
- chrome_location on google-chromen sijainti.
- Asenna myös python ja selenium (pip install selenium) jos ei niitä löydy.

muuta:
- Ison datamäärän kanssa voi kestää tosi kauan, koska jokaisen ilmoituksen sivu pitää
avata erikseen. (Muista ottaa "headless" pois kommentista)
- Tällä hetkellä kaikki ilmoituksista luetut palkkatiedot tallennetaan palkkatiedot.txt tiedostoon.
numerolliset_palkkatiedot.txt tiedostossa on palkkatiedot, jotka sisältävät numeroita.
Halutessa sivulta voi kerätä myös muuta tietoa. Tiedot eivät tule tiedostoon järjestyksessä.
"""

url = "https://paikat.te-palvelut.fi/tpt/?professions=3&announced=0&leasing=0&remotely=0&english=false&sort=8"
max_sample_size = 50
driver_location = '/usr/bin/chromedriver'
chrome_location = '/usr/bin/google-chrome'

start_time = time.time()

options = webdriver.ChromeOptions()
options.binary_location = chrome_location

#options.add_argument('--headless')# <---- lyhentää hieman suoritusaikaa! (piilottaa selaimen)
#time.sleep(3)# <---- tätä voi käyttää koodissa vian löytämiseen nettisivun navigoinnista

service = Service(executable_path=driver_location)
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(5)
driver.get(url)
deny_cookies_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.cc-btn.cc-deny")))
deny_cookies_button.click()

#Painelee "Lataa lisää" nappia niin kauan että se häviää tai ilmoituksia näkyy yli max_sample_size.
load_more_counter = 1
while True:
    try:
        if load_more_counter > (max_sample_size / 200 + 1):
            break
        load_more_button = driver.find_element(By.ID, "loadMoreButton")
        driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
        load_more_button.click()
        print('"Lataa lisää" nappia painettu: ', load_more_counter)
        load_more_counter += 1
        time.sleep(0.1)#vähentää erroreja
    except:
        print('Except (luultavasti kaikki sivun ilmoitukset näkyvillä)')
        break

page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')
links = soup.find_all('a')
subpages = set()

#Tallentaa kaikkien ilmoitusten linkit.
subpage_counter = 1
for link in links:
    if subpage_counter > max_sample_size:
        break
    href = link.get('href')
    if href is not None and "/tpt/" in href:
        subpages.add(href)
        subpage_counter += 1
print('avoimia työpaikkoja yhteensä:', subpage_counter-1)

#Tallentaa kaikki ilmoitetut palkkatiedot.
palkat = []
palkat_counter = 1
for subpage in subpages:
    driver.get("https://paikat.te-palvelut.fi" + subpage)
    subpage_source = driver.page_source
    subpage_soup = BeautifulSoup(subpage_source, "html.parser")
    tiedot_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Tiedot")))
    tiedot_button.click()
    tiedot_source = driver.page_source
    tiedot_soup = BeautifulSoup(tiedot_source, "html.parser")
    tags = tiedot_soup.find_all('div', {'class': 'col-xs-5'})
    for tag in tags:
        header = tag.get_text().strip()
        if header == 'Palkkaus':
            palkkaus = tag.find_next_sibling('div', {'class': 'col-xs-7 detailValue'})
            if palkkaus:
                palkka = palkkaus.get_text().strip()
                palkat.append(palkka)
                print('ilmoitettuja palkkatietoja yhteensä:', palkat_counter)
                palkat_counter += 1

print('\navoimia työpaikkoja yhteensä:', subpage_counter-1)
print('ilmoitettuja palkkatietoja yhteensä:', palkat_counter-1)

#Kirjoittaa palkkatiedot tiedostoon.
print('Tallennetaan kaikki palkkatiedot tiedostoon "palkkatiedot.txt"...')
with open('palkkatiedot.txt', 'w') as file:
    file.write('\n'.join(str(palkka) for palkka in palkat))
print('Tallennetaan kaikki numerolliset palkkatiedot tiedostoon "numerolliset_palkkatiedot.txt"...')
with open('numerolliset_palkkatiedot.txt', 'w') as file:
    file.write('\n'.join(palkka for palkka in palkat if re.search('\d', palkka)))
print('valmis')

driver.quit()

end_time = time.time()
print("Time taken: ", end_time - start_time, "seconds")