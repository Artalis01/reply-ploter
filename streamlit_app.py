import datetime
import joblib
import random
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
    This app is able to shows you a plot of replies stance from social media X
    where the main topic is 2024 president election in Indonesia.
    """
)
topic = []
tweet_replies = []
stances = []

url = st.text_input('URL')
if url != "":
    start_time = t.time()
    with st.status("Sedang memuat data...") as status:
        topic, tweet_replies = xc.xcrawl(status, url)
        st.session_state.topic = topic
        st.session_state.tweet_replies = tweet_replies

        status.update(label="(3/4) AI sedang bekerja. . .")
        features = pt.preprocess(status, topic, tweet_replies)
        
        status.update(label="(3/4) AI sedang memprediksi stance. . .")
        model = joblib.load("resources/model/model_svm.joblib")
        stances = model.predict(features)
        print("Prediksi Selesai!\n", stances)

        status.update(label="(4/4) Plotting. . .")

        end_time = t.time()
        time_spent = end_time - start_time
        label = "Proses selesai dalam"+" "+str(round(time_spent,2))+" "+"detik!" 
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
    st.info("Masukkan Link URL tweet pada kolom di atas")   

if 'stance_df' not in st.session_state:
    np.random.seed(42)

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

    data = {
        "username": [f"USER-{i}" for i in range(2100, 2080, -1)],
        "content": np.random.choice(reply_contents, size=20),
        "stance": np.random.choice(["Mendukung", "Menentang", "Netral"], size=20),
        "date": [
            datetime.date(2024, 1, 1) + datetime.timedelta(days=random.randint(0, 200))
            for _ in range(20)
        ],
    }
    topic = {
        'name': 'Pengguna',
        'content': 'Hari yang indah!',
    }
    stance_df = pd.DataFrame(data)
    st.session_state.stance_df = stance_df
    st.session_state.topic = topic

st.header('Topik')
st.write('User :\n', st.session_state.topic['name'])
st.write('Tweet:\n', st.session_state.topic['content'])

st.header('Daftar Reply')
st.write(f"Total Reply: `{len(st.session_state.stance_df)}`")

# specify columns to be displayed
columns_to_show = ['content', 'stance', 'date']

renamed_columns = {
    'content': 'Reply',
    'stance': 'Stance',
    'date': 'Tanggal',
}

df_to_display = st.session_state.stance_df[columns_to_show].rename(columns=renamed_columns)

# Show the replies dataframe
show_df = st.data_editor(
    df_to_display,
    use_container_width=True,
    hide_index=True,
    disabled=['Reply','Stance','Tanggal']
)

# Show metrics side by side using `st.columns` and `st.metric`.
col1, col2, col3 = st.columns(3)
num_favor = len(st.session_state.stance_df[st.session_state.stance_df.stance == "Mendukung"])
num_against = len(st.session_state.stance_df[st.session_state.stance_df.stance == "Menentang"])
num_none = len(st.session_state.stance_df[st.session_state.stance_df.stance == "Netral"])

col1.metric(label="Jumlah Reply Mendukung", value=num_favor)
col2.metric(label="Jumlah Reply Menentang", value=num_against)
col3.metric(label="Jumlah Reply Netral", value=num_none)

st.header('Statistik\n')

# Define the color conditions for the Job column
color = alt.Color('Stance:N',
    scale=alt.Scale(domain=['Mendukung', 'Menentang', 'Netral'],
                    range=['blue', 'red', 'gray']),
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


# Create a random Pandas dataframe with existing tickets.
if "df" not in st.session_state:
    pass
    # Set seed for reproducibility.
    np.random.seed(42)

    # Make up some fake issue descriptions.
    reply_contents = [
        "Network connectivity issues in the office",
        "Software application crashing on startup",
        "Printer not responding to print commands",
        "Email server downtime",
        "Data backup failure",
        "Login authentication problems",
        "Website performance degradation",
        "Security vulnerability identified",
        "Hardware malfunction in the server room",
        "Employee unable to access shared files",
        "Database connection failure",
        "Mobile application not syncing data",
        "VoIP phone system issues",
        "VPN connection problems for remote employees",
        "System updates causing compatibility issues",
        "File server running out of storage space",
        "Intrusion detection system alerts",
        "Inventory management system errors",
        "Customer data not loading in CRM",
        "Collaboration tool not sending notifications",
    ]

    # Generate the dataframe with 20 rows/tickets.
    data = {
        "ID": [f"TICKET-{i}" for i in range(1100, 1000, -1)],
        "Issue": np.random.choice(reply_contents, size=100),
        "Status": np.random.choice(["Open", "In Progress", "Closed"], size=100),
        "Priority": np.random.choice(["High", "Medium", "Low"], size=100),
        "Date Submitted": [
            datetime.date(2023, 6, 1) + datetime.timedelta(days=random.randint(0, 182))
            for _ in range(100)
        ],
    }
    df = pd.DataFrame(data)

    # Save the dataframe in session state (a dictionary-like object that persists across
    # page runs). This ensures our data is persisted when the app updates.
    st.session_state.df = df

# Show a section to add a new ticket.
# st.header("Add a ticket")

# We're adding tickets via an `st.form` and some input widgets. If widgets are used
# in a form, the app will only rerun once the submit button is pressed.
# with st.form("add_ticket_form"):
#     issue = st.text_area("Describe the issue")
#     priority = st.selectbox("Priority", ["High", "Medium", "Low"])
#     submitted = st.form_submit_button("Submit")

# if submitted:
#     pass
#     # Make a dataframe for the new ticket and append it to the dataframe in session
#     # state.
#     recent_ticket_number = int(max(st.session_state.df.ID).split("-")[1])
#     today = datetime.datetime.now().strftime("%m-%d-%Y")
#     df_new = pd.DataFrame(
#         [
#             {
#                 "ID": f"TICKET-{recent_ticket_number+1}",
#                 "Issue": issue,
#                 "Status": "Open",
#                 "Priority": priority,
#                 "Date Submitted": today,
#             }
#         ]
#     )

#     # Show a little success message.
#     st.write("Ticket submitted! Here are the ticket details:")
#     st.dataframe(df_new, use_container_width=True, hide_index=True)
#     st.session_state.df = pd.concat([df_new, st.session_state.df], axis=0)

# Show section to view and edit existing tickets in a table.
# st.header("Existing tickets")
# st.write(f"Number of tickets: `{len(st.session_state.df)}`")

# st.info(
#     "You can edit the tickets by double clicking on a cell. Note how the plots below "
#     "update automatically! You can also sort the table by clicking on the column headers.",
#     icon="✍️",
# )

# Show the tickets dataframe with `st.data_editor`. This lets the user edit the table
# cells. The edited data is returned as a new dataframe.
# edited_df = st.data_editor(
#     st.session_state.df,
#     use_container_width=True,
#     hide_index=True,
#     column_config={
#         "Status": st.column_config.SelectboxColumn(
#             "Status",
#             help="Ticket status",
#             options=["Open", "In Progress", "Closed"],
#             required=True,
#         ),
#         "Priority": st.column_config.SelectboxColumn(
#             "Priority",
#             help="Priority",
#             options=["High", "Medium", "Low"],
#             required=True,
#         ),
#     },
#     # Disable editing the ID and Date Submitted columns.
#     disabled=["ID", "Date Submitted"],
# )

# Show some metrics and charts about the ticket.
# st.header("Statistics")

# Show metrics side by side using `st.columns` and `st.metric`.
# col1, col2, col3 = st.columns(3)
# num_open_tickets = len(st.session_state.df[st.session_state.df.Status == "Open"])
# col1.metric(label="Number of open tickets", value=num_open_tickets, delta=10)
# col2.metric(label="First response time (hours)", value=5.2, delta=-1.5)
# col3.metric(label="Average resolution time (hours)", value=16, delta=2)

# Show two Altair charts using `st.altair_chart`.
# st.write("")
# st.write("##### Ticket status per month")
# status_plot = (
#     alt.Chart(edited_df)
#     .mark_bar()
#     .encode(
#         x="month(Date Submitted):O",
#         y="count():Q",
#         xOffset="Status:N",
#         color="Status:N",
#     )
#     .configure_legend(
#         orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
#     )
# )
# st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

# st.write("##### Current ticket priorities")
# priority_plot = (
#     alt.Chart(edited_df)
#     .mark_arc()
#     .encode(theta="count():Q", color="Priority:N")
#     .properties(height=300)
#     .configure_legend(
#         orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
#     )
# )

# st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")
