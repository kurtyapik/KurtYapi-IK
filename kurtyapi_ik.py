import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- BAĞLANTI AYARLARI ---
@st.cache_resource
def get_google_sheet():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"], strict=False)
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open("KurtYapi_IK_Merkez")

# --- SİSTEM KURULUMU ---
try:
    sh = get_google_sheet()
    # 1. Sekme: Personel Listesi
    ws_personel = sh.get_worksheet(0)
    # 2. Sekme: İzin Talepleri
    ws_talepler = sh.get_worksheet(1)
    
    # Personel verilerini yükle (Görseldeki başlıklara göre)
    df_personel = pd.DataFrame(ws_personel.get_all_records())
except Exception as e:
    st.error(f"Bağlantı hatası: {e}")
    st.stop()

st.title("🏗️ KURT YAPI İK YÖNETİMİ")

# --- PERSONEL SORGULAMA ---
tc_no = st.text_input("TC Kimlik No ile Giriş Yapınız:")

if tc_no:
    # Görseldeki 'TC Kimlik No' sütununu kullanıyoruz
    kayit = df_personel[df_personel['TC Kimlik No'].astype(str) == tc_no.strip()]
    
    if not kayit.empty:
        personel = kayit.iloc[0]
        st.success(f"Hoş geldiniz, {personel['Adı Soyadı']}!")
        
        with st.form("izin_formu"):
            izin_turu = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Hastalık/Rapor"])
            baslangic = st.date_input("Başlangıç Tarihi")
            bitis = st.date_input("Bitiş Tarihi")
            
            if st.form_submit_button("Talebi Gönder"):
                gun = (bitis - baslangic).days + 1
                # Talepler sayfasına yaz
                ws_talepler.append_row([
                    datetime.now().strftime("%d-%m-%Y"), 
                    personel['Adı Soyadı'], 
                    izin_turu, 
                    str(baslangic), 
                    str(bitis), 
                    gun, 
                    "⏳ Bekliyor"
                ])
                st.success("Talebiniz başarıyla yöneticiye iletildi.")
    else:
        st.error("Bu TC ile kayıtlı personel bulunamadı.")

# --- YÖNETİCİ PANELİ ---
st.divider()
admin_pin = st.text_input("Yönetici PIN:", type="password")
if admin_pin == "1923":
    st.subheader("⚙️ Onay Bekleyen Talepler")
    try:
        talep_data = ws_talepler.get_all_records()
        if talep_data:
            st.dataframe(pd.DataFrame(talep_data))
        else:
            st.info("Henüz bekleyen talep yok.")
    except:
        st.write("Talepler sayfası boş.")
