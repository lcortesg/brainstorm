import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from streamlit.components.v1 import html

st.set_page_config(
    page_title='Ideas',
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

# Authenticate and connect to Google Sheets
try:
    client = authenticate_google_sheets()
except Exception as e:
    st.error(f"Failed to authenticate with Google Sheets: {e}")
    st.stop()


def main():
    try:
        data = read_google_sheet(client, "Preguntas")
        questions = data["Preguntas"].to_list()
        question = questions[0]
        st.title(question)

        new_data = st.text_input("Describe en una palabra lo que significa para ti")
        if st.button("Enviar respuesta", type="primary"):
            write_google_sheet(client, new_data, "Respuestas")
    except Exception as e:
        st.error(f"Error reading spreadsheet: {e}")


if __name__ == "__main__":
    main()
