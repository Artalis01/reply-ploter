from selenium.webdriver.common.by import By
from seleniumbase import SB
import streamlit as st
import app_auth as auth
import time as t
import random
import re

def get_config():
    return {
        "repliesParentSelector": "//*[@id=\"react-root\"]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div",
        "postSelector": "//article[@data-testid='tweet']",
        }

def get_num_value(textList):
    # Get only numeric in a text
    if len(textList) > 0:
            numText = re.findall(r'\d+', textList[0])
    else:
        print("No Data")
        return [0]
    return numText

def is_element_visible(sb, element):
    return sb.execute_script("""
        var rect = arguments[0].getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    """, element)

def is_button_exist(sb):
    buttons = []
    parentSelector = get_config()['repliesParentSelector']
    buttonParent = sb.find_element(By.XPATH, parentSelector)
    buttons = buttonParent.find_elements(By.XPATH, "//button[@type= 'button']")
    # button_list = [button.text for button in buttons]

    for button in buttons:
        try:
            if button.is_displayed() and is_element_visible(sb, button):
                if ("Show more" in button.text) or ("Show" in button.text and "replies" not in button.text):
                    button.click()
                    sb.sleep(3)
                    button_exist = True
                    break

            else: button_exist = False
        except Exception as e:
            print(f"An error occurred: Button: {e}")
            button_exist = False

    return button_exist

def get_topic(sb):
    # Get a single post tweet as topic data
    tweet = {}
    counter = 0
    cell_inner_div = None
    while counter < 5:
        try:
            # Get element for each item
            cell_inner_div = sb.find_element(By.XPATH, ".//div[@data-testid='cellInnerDiv']")
            break
        except Exception as e:
            if counter >= 4:
                st.error('Terjadi kesalahan pada server. Mohon coba kembali')
                return None
            print(f"An error occurred: Get Topic: {e}")
            counter+=1

    tweet_userdatas = cell_inner_div.find_elements(By.XPATH, ".//div[@data-testid='User-Name']")
    tweet_dates = cell_inner_div.find_elements(By.XPATH, ".//time")
    tweet_texts = cell_inner_div.find_elements(By.XPATH, ".//div[@data-testid='tweetText']")

    # Get all data from all elements
    # split username and user nickname
    tweet_userdata = [element.text for element in tweet_userdatas]
    if len(tweet_userdata) > 0:
        tweet_user = tweet_userdata[0].split('\n')
    tweet_date = [element.text for element in tweet_dates]
    tweet_text = [element.text for element in tweet_texts]

    if len(tweet_text)>0:
        tweet['name'] = tweet_user[0]
        tweet['username'] = tweet_user[1]
        tweet['date'] = tweet_date[0]
        tweet['content'] = tweet_text[0].replace("\n", r". ")
        return tweet

def get_replies(sb, tweet_replies):
    # Return all replies from a single tweet
    parentSelector = get_config()['repliesParentSelector']
    tweet_parent = sb.find_element(By.XPATH, parentSelector)
    replies = tweet_parent.find_elements(By.XPATH, get_config()['postSelector'])

    media_counter = 0
    # Iterate over each cell_inner_div and extract the text of tweetText elements
    for reply_cell in replies:
        reply = {}
        
        reply_userdatas = reply_cell.find_elements(By.XPATH, ".//div[@data-testid='User-Name']")
        reply_dates = reply_cell.find_elements(By.XPATH, ".//time")
        reply_texts = reply_cell.find_elements(By.XPATH, ".//div[@data-testid='tweetText']")
        reply_urls = reply_cell.find_elements(By.XPATH, ".//a[contains(@href, 'status') and not(contains(@href, 'analytic')) and not(contains(@href, 'photo')) and not(contains(@href, 'media_tag'))]")
        reply_likes = reply_cell.find_elements(By.XPATH, ".//button[@data-testid = 'like']")

        reply_userdata = [element.text for element in reply_userdatas]
        if len(reply_userdata) > 0:
            reply_user = reply_userdata[0].split('\n')
        reply_date = [element.text for element in reply_dates]
        reply_text = [element.text for element in reply_texts]
        reply_url = [element.get_attribute('href') for element in reply_urls]
        reply_like = [element.get_attribute('aria-label') for element in reply_likes]

        reply_like = get_num_value(reply_like)

        if len(reply_url)>0: # and len(reply_view)>0:
            if "2023" not in reply_date[0]:
                reply_date[0] = reply_date[0]+", 2024"
            reply['url'] = reply_url[0]
            reply['name'] = reply_user[0]
            reply['username'] = reply_user[1]
            reply['date'] = reply_date[0]
            reply['likes'] = int(reply_like[0])

            if len(reply_text) > 0:
                reply['content'] = reply_text[0].replace("\n", r". ")
            else:
                reply['content'] = 'image/video'
                media_counter += 1

            if reply not in tweet_replies:
                if reply['url'] != sb.get_current_url():
                    if reply['content'] != 'image/video':
                        tweet_replies.append(reply)
                    
            else:
                continue
        else:
            print("ADVERTISEMENT")

    return media_counter

def scroll_replies(sb, pbar, tweet_replies, scrollPixels = 2450):
    #Scroll to get tweet replies data
    last_height = sb.execute_script("return document.body.scrollHeight")
    retried = False
    button_exist = False

    while True:
        try:
            media_counter = get_replies(sb, tweet_replies)
            pbar.progress(int((4/11)*100), text=f'(4/11) Mengambil komentar. Total komentar: {len(tweet_replies)}')

            sb.execute_script(f"window.scrollTo(0, {scrollPixels});")
            new_height = sb.execute_script("return document.body.scrollHeight")
            sb.sleep(round(random.uniform(0, 1), 2))
            if new_height-scrollPixels <1200 and scrollPixels < last_height:
                button_exist = is_button_exist(sb)
            elif new_height == last_height and scrollPixels > last_height:
                button_exist = is_button_exist(sb)
                if retried == False and button_exist==False:
                    retried = True
                    continue
                elif retried == True:
                    break
            last_height = new_height
            retried = False
            if media_counter > 0:
                scrollPixels = scrollPixels+1000+(media_counter*250)
                continue
            scrollPixels = scrollPixels+1000
        except Exception as e:
            print(f"An error occurred: Scroll: {e}")

def login(sb, check_status=False):
    sb.wait(3)
    if not sb.is_element_present('a[data-testid="loginButton"]') and not sb.is_element_present('a[data-testid="login"]'):
        if check_status:
            return True
        st.info("Anda sudah login")
        return None
    
    if check_status:
        st.info(r"Mohon login terlebih dahulu! gunakan perintah 'xclogin' pada kolom di atas")
        with st.status("Error. . .") as status:
            status.update(label='Xcrawler belum login', expanded=True, state='error')
        return False
    else:
        profile = auth.set_auth()
        if len(profile['username']) < 1:
            st.info("Mohon isi form terlebih dahulu!")
            return False

        sb.click('a[data-testid="loginButton"]')
        sb.wait(3)
        sb.type('input[autocomplete="username"]', profile['username'])
        sb.click('button:contains("Next")')
        sb.wait(3)
        if sb.is_element_present('input[data-testid="ocfEnterTextTextInput"]'):
            sb.type('input[data-testid="ocfEnterTextTextInput"]', profile['email'])
            sb.click('button:contains("Next")')

        sb.wait(3)
        sb.type('input[autocomplete="current-password"]', profile['password'])
        sb.click('button[data-testid="LoginForm_Login_Button"]')
        sb.wait(3)
        if sb.is_element_present('input[data-testid="ocfEnterTextTextInput"]'):
            sb.type('input[data-testid="ocfEnterTextTextInput"]', profile['email'])
            sb.click('button:contains("Next")')

        sb.wait_for_element_absent('div[aria-labelledby="modal-header"]', timeout=120)

        return True

def logout():
    with SB(headless=True, user_data_dir='resources/xcrawler/user/profile1') as sb:
        sb.open("https://x.com/")
        sb.wait(3)
        if not sb.is_element_present('button[data-testid="SideNav_AccountSwitcher_Button"]'):
            st.info("Not logged in")
            return None
    
        else:
            sb.click('button[data-testid="SideNav_AccountSwitcher_Button"]')
            sb.wait(2)
            sb.click('a[href="/logout"]')
            sb.wait(2)
            sb.click('button[data-testid="confirmationSheetConfirm"]')
            sb.wait(10)
            st.Info("Xcrawler logout succesfully")

def is_url_invalid(sb, pbar):
    if sb.is_element_present('div[data-testid="error-detail"]'):
        pbar.empty()
        with st.status("Error...") as status:
            status.update(label="URL tidak valid", expanded=True, state="error")
        st.warning("Pastikan link URL sudah benar!")
        return True
    return False

def get_replies_data(sb, pbar, tweet_replies):
    # return all replies from a tweet
    # start_time = t.time()

    scroll_replies(sb, pbar, tweet_replies)

    # end_time = t.time()
    # time_spent = end_time - start_time
    # print("Time spent for a single tweet:", round(time_spent), "seconds")

def xcrawl(url, pbar=None, check_login_status=False):    
    tweet_replies = []
    topic = []
    with SB(headless=True, uc=True, user_data_dir='resources/xcrawler/user/profile1') as sb:
        if check_login_status:
            sb.uc_open_with_reconnect("https://x.com/", 2)
            login_status = login(sb)
            if login_status:
                st.info("Login Sukses!")
        else:
            sb.open(url)
            pbar.progress(int((2/11)*100), text='Sedang mempersiapkan data')
            login_status = login(sb, check_status=True)

            if not login_status:
                return[None, None]

            if not is_url_invalid(sb, pbar):
                pbar.progress(int((3/11)*100), text='(3/11) Mengambil topik tweet')
                topic = get_topic(sb)
                if topic == None:
                    return [None, None]

                pbar.progress(int((4/11)*100), text='(4/11) Mengambil komentar tweet')
                get_replies_data(sb, pbar, tweet_replies)

                if len(tweet_replies) < 1:
                    tweet_replies = 'empty'

                return topic, tweet_replies
    return [None, None]
