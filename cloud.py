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
    layout="wide",
)
st.markdown("""
<style>
header, footer {
    display: none !important;
}
[data-testid="stAppViewContainer"] > .main {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
a[href*="streamlit.io"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

html('''
<script>
    window.top.document.querySelectorAll(`[href*="streamlit.io"]`).forEach(e => e.setAttribute("style", "display: none;"));
</script>
''', height=0, width=0)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
URL = st.secrets["google_service_account"]["sheet_url"]


@st.cache_resource
def authenticate_google_sheets():
    service_account_info = st.secrets["google_service_account"]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client


def read_google_sheet(sheet, sheet_name):
    worksheet = sheet.worksheet(sheet_name)
    all_values = worksheet.get_all_values()
    if not all_values or len(all_values) < 2:
        return pd.DataFrame()
    headers = all_values[0]
    rows = all_values[1:]
    df = pd.DataFrame(rows, columns=headers)
    return df


def write_google_sheet(sheet, data, sheet_name):
    worksheet = sheet.worksheet(sheet_name)
    dataf = worksheet.get_all_values()
    index = len(dataf)
    datas = data.split()

    for i in range(len(datas)):
        worksheet.update_cell(index + 1, i + 1, datas[i])
    st.success("Respuesta enviada!")
    st.balloons()


def create_word_freq(dataframe):
    all_text = " ".join(
        dataframe.fillna("").astype(str).apply(lambda row: " ".join(row), axis=1)
    )
    words = re.findall(r'\b\w+\b', all_text.lower())
    word_freq = dict(Counter(words))
    return word_freq


try:
    client = authenticate_google_sheets()
    sheet = client.open_by_url(URL)  # Open once here and reuse
except Exception as e:
    st.error(f"Failed to authenticate with Google Sheets: {e}")
    st.stop()


def create_word_cloud(ans, colormap='viridis', title=None):
    word_freq = create_word_freq(ans)
    wc = WordCloud(
        font_path='Verdana.ttf',
        width=1920,
        height=1080,
        background_color='white',
        colormap=colormap
    )
    wc.generate_from_frequencies(word_freq)
    fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=300)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    if title:
        ax.set_title(title, fontsize=34, weight='bold', pad=20)
    return fig


def word_cloud(title, fetch=10, update=1):
    placeholder = st.empty()
    last_fetch_time = 0
    cache_data = None
    FETCH_INTERVAL = fetch
    UPDATE_INTERVAL = update

    while True:
        current_time = time.time()
        if (current_time - last_fetch_time) >= FETCH_INTERVAL:
            cache_data = read_google_sheet(sheet, "Respuestas")  # Use opened sheet
            last_fetch_time = current_time

        if cache_data is not None and not cache_data.empty:
            fig = create_word_cloud(cache_data, "viridis", title)
            with placeholder.container():
                st.pyplot(fig)
            plt.close(fig)

        time.sleep(UPDATE_INTERVAL)


def main():
    try:
        data = read_google_sheet(sheet, "Preguntas")  # Use opened sheet
        question = data["Preguntas"].to_list()[0]
        fetch = int(data["fetch"].to_list()[0])
        update = int(data["update"].to_list()[0])
        word_cloud(question, fetch, update)
    except Exception as e:
        st.error(f"Error reading spreadsheet: {e}")


if __name__ == "__main__":
    main()
