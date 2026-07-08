
import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- BAĞLANTI ---
@st.cache_resource
def get_google_sheet():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"], strict=False)
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open("KurtYapi_IK_Merkez")

# --- SİSTEM KURULUMU ---
try:
    sh = get_google_sheet()
    ws_personel = sh.get_worksheet(0) # 1. Sekme
    ws_talepler = sh.get_worksheet(1) # 2. Sekme
    df_personel = pd.DataFrame(ws_personel.get_all_records())
except Exception as e:
    st.error("Veri tabanı bağlantı hatası! Sekmelerinizin sırasını kontrol edin.")
    st.stop()

st.title("🏗️ KURT YAPI İK YÖNETİMİ")

# --- PERSONEL SORGULAMA ---
tc_no = st.text_input("TC Kimlik Numaranızı Giriniz:")

if tc_no:
    kayit = df_personel[df_personel['TC_Kimlik'].astype(str) == tc_no.strip()]
    
    if not kayit.empty:
        personel = kayit.iloc[0]
        st.success(f"Hoş geldiniz, {personel['Ad_Soyad']}!")
        
        with st.form("izin_formu"):
            izin_turu = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Hastalık/Rapor"])
            baslangic = st.date_input("Başlangıç Tarihi")
            bitis = st.date_input("Bitiş Tarihi")
            
            if st.form_submit_button("Talebi Gönder"):
                gun = (bitis - baslangic).days + 1
                ws_talepler.append_row([datetime.now().strftime("%d-%m-%Y"), personel['Ad_Soyad'], izin_turu, str(baslangic), str(bitis), gun, "⏳ Bekliyor"])
                st.success("Talebiniz başarıyla kaydedildi.")
    else:
        st.error("Bu TC ile kayıtlı personel bulunamadı. Lütfen yönetici ile görüşün.")

# --- YÖNETİCİ PANELİ ---
st.divider()
if st.text_input("Yönetici Girişi (PIN):", type="password") == "1923":
    st.subheader("⚙️ Onay Bekleyen Talepler")
    try:
        talep_data = ws_talepler.get_all_records()
        if talep_data:
            st.dataframe(pd.DataFrame(talep_data))
        else:
            st.info("Henüz bekleyen talep yok.")
    except:
        st.write("Talepler sekmesi henüz boş.")
