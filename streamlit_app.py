import datetime
import joblib
import random
import re
import time as t
import altair as alt
import numpy as np
import pandas as pd
import preprocess_text as pt
import streamlit as st
import xcrawler as xc

# Show app title and description.
st.set_page_config(page_title="Repploter", page_icon="🎫")
st.title("🎫 Repploter")
st.write(
    """
    Aplikasi ini dapat menampilkan grafik distribusi stance reply atau komentar dari sosial media X dengan
    topik utama Pemilihan Umum Presiden Indonesia Tahun 2024.
    """
)
topic = []
tweet_replies = []
stances = []

if 'stance_df' not in st.session_state:
    np.random.seed(42)
    st.session_state.empty_content = False
    st.session_state.tweet_replies = tweet_replies
    st.session_state.info = 'empty url'
    reply_contents = [
        "Mantab!",
        "Yang benar saja",
        "Apa iya?",
        "Beneran",
        "Gitu juga bole",
        "Ah masa",
        "Gas pol",
        "Gaskeun",
        "Setuju tapi gimana ya",
        "Ah omdo",
        "Gas gak sih?",
        "Iya kah?",
        "Nah seharusnya gini gak sih?"
    ]

    stances = [
        "Mendukung",
        "Netral",
        "Menentang",
        "Netral",
        "Mendukung",
        "Menentang",
        "Mendukung",
        "Mendukung",
        "Netral",
        "Menentang",
        "Mendukung",
        "Netral",
        "Mendukung"
    ]

    data = {
        "username": [f"USER-{i}" for i in range(2100, 2087, -1)],
        "content": reply_contents,
        "stance": stances,
        "date": [
            datetime.date(2024, 1, 1) + datetime.timedelta(days=random.randint(0, 200))
            for _ in range(13)
            ],
        "likes": [random.randint(1, 100) for _ in range(13)],
    }
    topic = {
        'name': 'John',
        'content': 'Hari yang indah!',
    }
    stance_df = pd.DataFrame(data)
    st.session_state.stance_df = stance_df
    st.session_state.topic = topic

url = st.text_input('Link URL Tweet')
submit_button = st.button("Submit")

if url != '':
    if url == "xclogout":
        pass
    elif url == 'xclogin':
        xc.xcrawl('https://x.com/', check_login_status=True)
    elif not re.match(r'^https:\/\/x\.com(?:\/\S*)?$', url):
        st.warning('"Pastikan Link URL sudah benar dan berasal dari sosial media X atau Twitter!"')
        st.text("Contoh Format URL:\n https://x.com/user/status/888xxxx")
else:
    st.info('Masukkan Link URL Tweet pada kolom yang disediakan')

# in submit buttton add login function separate from xcrawl

# Action on button press
if submit_button:
    if url != "":
        if url == "xclogout":
            xc.logout()
        elif url == "xclogin":
            # xc.xcrawl('https://x.com/', check_login_status=True)
            pass
        elif re.match(r'^https:\/\/x\.com(?:\/\S*)?$', url):
            start_time = t.time()
            pbar = st.progress(0, text='Sedang memuat data')
            topic, tweet_replies = xc.xcrawl(url, pbar)

            if topic != None:
                st.session_state.empty_content = False
                st.session_state.topic = topic
                st.session_state.tweet_replies = tweet_replies
                if tweet_replies == 'empty':
                    pbar.empty()
                    with st.status(label="Tidak ada reply yang ditemukan") as status:
                        status.update(state='complete')
                    
                else:
                    pbar.progress(int((5/11)*100), text='(5/11) AI sedang bekerja')
                    features = pt.preprocess(pbar, topic, tweet_replies)
                    
                    pbar.progress(int((10/11)*100), text='(10/11) AI sedang memprediksi stance')
                    model = joblib.load("resources/model/model_svm.joblib")
                    stances = model.predict(features)

                    pbar.progress(int((11/11)*100), text='(11/11) Selesai')
                    pbar.empty()

                    end_time = t.time()
                    time_spent = end_time - start_time
                    label = "Proses selesai dalam"+" "+str(round(time_spent,2))+" "+"detik!" 
                    with st.status("Plotting...") as status:
                        status.update(label=label, state='complete')

                    adjusted_stances = []
                    # adjust stance value
                    for i in range(len(stances)):
                        stance = str(stances[i])
                        if stance == 'favor':
                            adjusted_stances.append('Mendukung')
                        elif stance == 'against':
                            adjusted_stances.append('Menentang')
                        else:
                            adjusted_stances.append('Netral')

                    # add predicted stances into replies data
                    for i, reply in enumerate(tweet_replies):
                        reply['stance'] = adjusted_stances[i]
                    
                    stance_df = pd.DataFrame(tweet_replies)
                    st.session_state.stance_df = stance_df 
            
            else:
                st.session_state.empty_content = True
            pbar.empty()
        else:
            st.session_state.empty_content = True
    else:
        st.session_state.empty_content = True

if 'empty_content' in st.session_state:
    if st.session_state.empty_content:
        st.image('resources/images/no_content.png', use_column_width=True) 

    elif not st.session_state.empty_content:
        st.header('Topik')
        st.markdown(f"**User :**")
        st.markdown(st.session_state.topic['name'])
        st.markdown('**Tweet:**')
        st.markdown(st.session_state.topic['content'])

        if st.session_state.tweet_replies == 'empty':
            st.info("Tidak ada reply dalam tweet")

        else:
            # get and show the most liked reply for each stance
            favor_df = st.session_state.stance_df[st.session_state.stance_df['stance'] == 'Mendukung']
            against_df = st.session_state.stance_df[st.session_state.stance_df['stance'] == 'Menentang']
            none_df = st.session_state.stance_df[st.session_state.stance_df['stance'] == 'Netral']
            
            st.header('Komentar Terpopuler')

            if len(favor_df) > 0:
                liked_favor = favor_df.loc[favor_df['likes'].idxmax()]
                st.markdown("**Mendukung:**")
                st.success(liked_favor['content'])
            if len(against_df) > 0:
                liked_against = against_df.loc[against_df['likes'].idxmax()]
                st.markdown("**Menentang:**")
                st.error(liked_against['content'])
            if len(none_df) > 0:
                liked_none = none_df.loc[none_df['likes'].idxmax()]
                st.markdown("**Netral:**")
                st.info(liked_none['content'])

            # specify columns to be displayed
            columns_to_show = ['content', 'stance', 'date']

            renamed_columns = {
                'content': 'Reply',
                'stance': 'Stance',
                'date': 'Tanggal',
            }

            renamed_df = st.session_state.stance_df[columns_to_show].rename(columns=renamed_columns)

            # Show reply list
            st.header('Daftar Reply')
            st.write(f"Total Reply: `{len(st.session_state.stance_df)}`")

            # define column color for stance
            def highlight_stance(val):
                if val == 'Mendukung':
                    return 'background-color: rgba(0, 0, 255, 0.3); color: black'
                if val == 'Menentang':
                    return 'background-color: rgba(255, 0, 0, 0.3); color: black'
                return ''  # No color for other values

            styled_df = renamed_df.style.map(highlight_stance, subset=['Stance'])

            # show dataframe
            # st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Show the replies dataframe
            show_df = st.data_editor(
                renamed_df,
                use_container_width=True,
                hide_index=True,
                disabled=['Reply','Stance','Tanggal']
            )

            # Show metrics side by side using `st.columns` and `st.metric`.
            col1, col2, col3 = st.columns(3)
            num_favor = len(st.session_state.stance_df[st.session_state.stance_df.stance == "Mendukung"])
            num_against = len(st.session_state.stance_df[st.session_state.stance_df.stance == "Menentang"])
            num_none = len(st.session_state.stance_df[st.session_state.stance_df.stance == "Netral"])

            col1.metric(label="**Jumlah Reply Mendukung**", value=num_favor)
            col2.metric(label="**Jumlah Reply Menentang**", value=num_against)
            col3.metric(label="**Jumlah Reply Netral**", value=num_none)

            st.header('Statistik\n')

            # Define the color conditions for the Job column
            color = alt.Color('Stance:N',
                scale=alt.Scale(domain=['Mendukung', 'Menentang', 'Netral'],
                                range=['green', 'red', 'blue']),
            )

            status_plot = (
                alt.Chart(show_df)
                .mark_bar()
                .encode(
                    x="Stance:O",
                    y=alt.Y('count():Q', axis=alt.Axis(title='Jumlah Reply')),
                    # xOffset="Stance:N",
                    color=color,
                )
                .configure_legend(
                    orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
                )
            )
            st.altair_chart(status_plot, use_container_width=True, theme="streamlit")