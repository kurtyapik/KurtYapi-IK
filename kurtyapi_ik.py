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

# --- HESAPLAMA ---
def hesapla_izin_hakkı(giris_tarihi_str):
    try:
        giris = pd.to_datetime(giris_tarihi_str).date()
        bugun = date.today()
        kıdem = bugun.year - giris.year - ((bugun.month, bugun.day) < (giris.month, giris.day))
        if kıdem < 1: return 0
        if 1 <= kıdem <= 5: return 14
        if 5 < kıdem < 15: return 20
        return 26
    except: return 0

sh = get_google_sheet()
ws_personel = sh.get_worksheet(0)
ws_talepler = sh.get_worksheet(1)
df_personel = pd.DataFrame(ws_personel.get_all_records())

st.title("🏗️ KURT YAPI İK YÖNETİMİ")

# --- TC SORGULAMA (Butonlu) ---
tc_input = st.text_input("TC Kimlik No Giriniz:")
if st.button("Sorgula"):
    st.session_state.tc = tc_input

if 'tc' in st.session_state and st.session_state.tc:
    kayit = df_personel[df_personel['TC Kimlik No'].astype(str) == st.session_state.tc.strip()]
    if not kayit.empty:
        p = kayit.iloc[0]
        hak = hesapla_izin_hakkı(p['Giriş Tarihi'])
        st.success(f"Hoş geldiniz, {p['Adı Soyadı']}! | Hak Edilen Yıllık İzin: {hak} gün.")
        
        with st.form("izin_talebi"):
            izin_turu = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni"])
            baslangic = st.date_input("Başlangıç")
            bitis = st.date_input("Bitiş")
            istenen_gun = (bitis - baslangic).days + 1
            
            # Avans İzin Uyarısı
            tür = "Avans İzin" if istenen_gun > hak else "Yıllık İzin"
            if tür == "Avans İzin":
                st.warning("⚠️ YASAL UYARI: İzin hakkınız bulunmamaktadır. Talep etmeniz durumunda bu süre 'Avans İzin' olarak işlenir ve iş akdinizin feshi durumunda maaşınızdan kesilecektir.")
            
            if st.form_submit_button("Talebi Gönder"):
                ws_talepler.append_row([datetime.now().strftime("%d-%m-%Y"), p['Adı Soyadı'], tür, str(baslangic), str(bitis), istenen_gun, "⏳ Bekliyor"])
                st.success("Talebiniz kaydedildi.")
    else:
        st.error("Personel bulunamadı.")

# --- YÖNETİCİ PANELİ ---
st.divider()
if st.text_input("Yönetici PIN:", type="password") == "1923":
    st.subheader("⚙️ Onay Paneli")
    df_talepler = pd.DataFrame(ws_talepler.get_all_records())
    if not df_talepler.empty:
        st.dataframe(df_talepler)
        secili = st.selectbox("Talep ID/Sıra seçin:", df_talepler.index)
        c1, c2 = st.columns(2)
        if c1.button("✅ Onayla"):
            ws_talepler.update_cell(int(secili) + 2, 7, "✅ Onaylandı")
            st.rerun()
        if c2.button("❌ Reddet"):
            ws_talepler.update_cell(int(secili) + 2, 7, "❌ Reddedildi")
            st.rerun()
