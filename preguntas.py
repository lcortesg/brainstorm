import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from streamlit.components.v1 import html

st.set_page_config(
    page_title='Pregunta',
    layout="wide",
)

# Hide Streamlit header/footer and remove padding/margin
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


def write_question(sheet, question):
    worksheet = sheet.worksheet("Preguntas")
    # Update the question in cell A2 (row=2, col=1)
    if question.strip():
        worksheet.update_cell(2, 1, question.strip())
        st.success("Pregunta cambiada!")
        st.balloons()
    else:
        st.warning("La pregunta no puede estar vacía.")


def clear_responses(sheet):
    worksheet = sheet.worksheet("Respuestas")
    worksheet.clear()
    worksheet.update_cell(1, 1, "Respuestas")
    st.success("Respuestas eliminadas!")
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
        questions = data["Preguntas"].to_list() if not data.empty else []
        question = questions[0] if questions else ""

        st.title("Cambio de pregunta", anchor=False)
        new_question = st.text_input("Escribe la pregunta que desees", question)

        if st.button("Cambiar pregunta", type="primary"):
            write_question(sheet, new_question)

        if st.button("Limpiar respuestas", type="primary"):
            clear_responses(sheet)

    except Exception as e:
        st.error(f"Error reading spreadsheet: {e}")


if __name__ == "__main__":
    main()
