import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials
import json

# --- BAĞLANTI ---
@st.cache_resource
def get_google_sheet():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"], strict=False)
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open("KurtYapi_IK_Merkez")

# --- İZİN HESAPLAMA MOTORU ---
def hesapla_izin_hakkı(giris_tarihi_str):
    try:
        giris_tarihi = pd.to_datetime(giris_tarihi_str).date()
        bugun = date.today()
        kıdem_yılı = bugun.year - giris_tarihi.year - ((bugun.month, bugun.day) < (giris_tarihi.month, giris_tarihi.day))
        
        if kıdem_yılı < 1: return 0
        if 1 <= kıdem_yılı <= 5: return 14
        if 5 < kıdem_yılı < 15: return 20
        return 26
    except:
        return 0

# --- SİSTEM ---
sh = get_google_sheet()
ws_personel = sh.get_worksheet(0)
ws_talepler = sh.get_worksheet(1)
df_personel = pd.DataFrame(ws_personel.get_all_records())

st.title("🏗️ KURT YAPI İK YÖNETİMİ")

tc_no = st.text_input("TC Kimlik No:")
if tc_no:
    kayit = df_personel[df_personel['TC Kimlik No'].astype(str) == tc_no.strip()]
    if not kayit.empty:
        p = kayit.iloc[0]
        izin_hakkı = hesapla_izin_hakkı(p['Giriş Tarihi'])
        st.success(f"Hoş geldiniz, {p['Adı Soyadı']}! | Yıllık İzin Hakkınız: {izin_hakkı} Gün")
        
        with st.form("izin_formu"):
            izin_turu = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni"])
            baslangic = st.date_input("Başlangıç")
            bitis = st.date_input("Bitiş")
            if st.form_submit_button("Talebi Gönder"):
                ws_talepler.append_row([datetime.now().strftime("%d-%m-%Y"), p['Adı Soyadı'], izin_turu, str(baslangic), str(bitis), (bitis-baslangic).days + 1, "⏳ Bekliyor"])
                st.success("Talebiniz kaydedildi.")
    else:
        st.error("Personel bulunamadı.")

# --- YÖNETİCİ ---
st.divider()
if st.text_input("Yönetici PIN:", type="password") == "1923":
    st.subheader("⚙️ Onay Paneli")
    df_talepler = pd.DataFrame(ws_talepler.get_all_records())
    if not df_talepler.empty:
        st.dataframe(df_talepler)
        secili = st.selectbox("İşlem:", df_talepler.index)
        if st.button("✅ Onayla"):
            ws_talepler.update_cell(int(secili) + 2, 7, "✅ Onaylandı")
            st.rerun()
