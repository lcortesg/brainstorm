import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from streamlit.components.v1 import html

st.set_page_config(
    page_title='Ideas',
    layout="wide",
)

# Hide Streamlit branding and remove padding/margin
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


def open_sheet(client, url):
    return client.open_by_url(url)


def read_google_sheet(sheet, worksheet_name):
    worksheet = sheet.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)


def write_google_sheet(sheet, data, worksheet_name):
    worksheet = sheet.worksheet(worksheet_name)
    datas = data.split()
    worksheet.append_row(datas)
    st.success("Respuesta enviada!")
    st.balloons()


try:
    client = authenticate_google_sheets()
    sheet = open_sheet(client, URL)
except Exception as e:
    st.error(f"Failed to authenticate with Google Sheets: {e}")
    st.stop()


def main():
    try:
        data = read_google_sheet(sheet, "Preguntas")
        questions = data["Preguntas"].to_list()
        question = questions[0] if questions else "No hay preguntas disponibles."

        st.image("fabrica2.png")
        st.title(question, anchor=False)

        new_data = st.text_input("Describe en una palabra lo que significa para ti")

        if st.button("Enviar respuesta", type="primary"):
            if new_data.strip():
                write_google_sheet(sheet, new_data, "Respuestas")
            else:
                st.warning("Por favor ingresa una respuesta antes de enviar.")

    except Exception as e:
        st.error(f"Error reading spreadsheet: {e}")


if __name__ == "__main__":
    main()
