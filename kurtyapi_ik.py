
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# Bağlantı Ayarları
@st.cache_resource
def get_google_sheet():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"], strict=False)
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open("KurtYapi_IK_Merkez")

sh = get_google_sheet()
ws_personel = sh.worksheet("Personel_Bilgileri")
df_personel = pd.DataFrame(ws_personel.get_all_records())

st.title("🏗️ KURT YAPI İZİN SİSTEMİ")

# TC Sorgulama
tc_input = st.text_input("TC Kimlik No Giriniz:")

if tc_input:
    # Veriyi TC ile eşleştirme
    kayit = df_personel[df_personel['TC_Kimlik'].astype(str) == tc_input.strip()]
    
    if not kayit.empty:
        personel = kayit.iloc[0]
        st.success(f"Hoş geldiniz, {personel['Ad_Soyad']}! (Kalan İzin: {personel['Toplam_İzin_Hakkı']} gün)")
        
        # İzin Talep Formu
        with st.form("izin_talebi"):
            baslangic = st.date_input("Başlangıç")
            bitis = st.date_input("Bitiş")
            if st.form_submit_button("Talebi Gönder"):
                # Talep Excel'e kaydedilir
                sh.worksheet("Talepler").append_row([tc_input, personel['Ad_Soyad'], str(baslangic), str(bitis), "Bekliyor"])
                st.success("Talebiniz yöneticiye iletildi.")
    else:
        st.error("Bu TC ile kayıtlı personel bulunamadı.")
