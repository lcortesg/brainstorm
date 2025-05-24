import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
from collections import Counter
import time
from streamlit.components.v1 import html

st.set_page_config(
    page_title='Nube',
    # page_icon=im,
    layout="wide",
)
hide_streamlit_style = """
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

html('''
<script>
    window.top.document.querySelectorAll(`[href*="streamlit.io"]`).forEach(e => e.setAttribute("style", "display: none;"));
</script>
''')

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",  # For Google Sheets API
    "https://www.googleapis.com/auth/drive.file",   # For Google Drive file access
]
URL = st.secrets["google_service_account"]["sheet_url"]


# Authenticate with Google Sheets
def authenticate_google_sheets():
    # Use Streamlit secrets for authentication
    service_account_info = st.secrets["google_service_account"]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client

# Read data from Google Spreadsheet
def read_google_sheet(client, name):
    sheet = client.open_by_url(URL)#.sheet1  # Open the first sheet
    worksheet = sheet.worksheet(name)
    data = worksheet.get_all_records()  # Fetch all data as a list of dictionaries
    return pd.DataFrame(data)

# Write data to Google Spreadsheet
def write_google_sheet(client, data, name):
    sheet = client.open_by_url(URL)#.sheet1
    worksheet = sheet.worksheet(name)
    dataf = worksheet.get_all_records()
    dataf = pd.DataFrame(dataf)
    index = dataf.shape[0]
    datas = data.split()

    for i in range(len(datas)):
        worksheet.update_cell(index+2, i+1, datas[i])
    st.success("Respuesta enviada!")
    st.balloons()

def create_word_freq(dataframe):
    """
    Create a word frequency dictionary from all text data in a DataFrame.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing text data.

    Returns:
        dict: A dictionary where keys are words and values are their frequencies.
    """
    # Concatenate all text from all columns
    all_text = " ".join(
        dataframe.fillna("").astype(str).apply(lambda row: " ".join(row), axis=1)
    )

    # Tokenize: convert to lowercase and split by non-alphanumeric characters
    words = re.findall(r'\b\w+\b', all_text.lower())

    # Count word frequencies
    word_freq = dict(Counter(words))

    return word_freq

# Authenticate and connect to Google Sheets
try:
    client = authenticate_google_sheets()
except Exception as e:
    st.error(f"Failed to authenticate with Google Sheets: {e}")
    st.stop()


def create_word_cloud_old(ans, colormap='viridis'):
    word_freq = create_word_freq(ans)
    wc = WordCloud(font_path='Verdana.ttf', width=3840, height=1400, background_color='white', colormap=colormap)
    wc.generate_from_frequencies(word_freq)
    # Plot using matplotlib
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    return fig

def create_word_cloud(ans, colormap='viridis', title=None):
    word_freq = create_word_freq(ans)

    # Use high resolution for WordCloud
    wc = WordCloud(
        font_path='Verdana.ttf',
        width=1920,  # Adjust resolution to match display
        height=1080,
        background_color='white',
        colormap=colormap
    )
    wc.generate_from_frequencies(word_freq)

    # Plot using matplotlib with matching figsize
    fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=300)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')

    # Add title if provided
    if title:
        ax.set_title(title, fontsize=34, weight='bold', pad=20)
    return fig

def word_cloud(title):
    placeholder = st.empty()
    last_fetch_time = 0
    cache_data = None
    FETCH_INTERVAL = 10  # Fetch new data every 10 seconds
    UPDATE_INTERVAL = 1  # Update the word cloud every 1 second

    while True:
        current_time = time.time()

        # Fetch new data from Google Sheets every FETCH_INTERVAL seconds
        if (current_time - last_fetch_time) >= FETCH_INTERVAL:
            cache_data = read_google_sheet(client, "Respuestas")
            last_fetch_time = current_time

        # Update the word cloud with the latest data every UPDATE_INTERVAL seconds
        if cache_data is not None and not cache_data.empty:
            fig = create_word_cloud(cache_data, "viridis", title)
            with placeholder.container():
                st.pyplot(fig)
            plt.close(fig)  # Close the figure to free memory

        time.sleep(UPDATE_INTERVAL)

def main():
    try:
        data = read_google_sheet(client, "Preguntas")
        questions = data["Preguntas"].to_list()
        question = questions[0]
        #st.title(question)
        word_cloud(question)


    except Exception as e:
        st.error(f"Error reading spreadsheet: {e}")


if __name__ == "__main__":
    main()
