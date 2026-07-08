import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials
import json

# Sayfa Ayarları
st.set_page_config(page_title="Kurt Yapı İK", page_icon="🏗️", layout="centered")

# --- GOOGLE SHEETS BAĞLANTISI ---
@st.cache_resource
def get_google_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_str = st.secrets["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(creds_str, strict=False)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("KurtYapi_IK_Merkez")

# Veritabanına Bağlan
try:
    sh = get_google_sheet()
    ws_talepler = sh.worksheet("Talepler")
    ws_bakiyeler = sh.worksheet("Bakiyeler")
    
    if len(ws_talepler.get_all_values()) == 0:
        ws_talepler.append_row(["ID", "Tarih", "Personel Adı", "İzin Türü", "Başlangıç", "Bitiş", "Gün", "Durum"])
    if len(ws_bakiyeler.get_all_values()) == 0:
        ws_bakiyeler.append_row(["Personel Adı", "Toplam İzin Hakkı", "Kullanılan", "Kalan Bakiye"])
except Exception as e:
    st.error(f"Veri tabanına bağlanılamadı: {e}")
    st.stop()

# Verileri Okuma
veri_talepler = ws_talepler.get_all_values()
df_talepler = pd.DataFrame(veri_talepler[1:], columns=veri_talepler[0]) if len(veri_talepler) > 1 else pd.DataFrame(columns=["ID", "Tarih", "Personel Adı", "İzin Türü", "Başlangıç", "Bitiş", "Gün", "Durum"])

veri_bakiyeler = ws_bakiyeler.get_all_values()
df_bakiyeler = pd.DataFrame(veri_bakiyeler[1:], columns=veri_bakiyeler[0]) if len(veri_bakiyeler) > 1 else pd.DataFrame(columns=["Personel Adı", "Toplam İzin Hakkı", "Kullanılan", "Kalan Bakiye"])

st.title("🏗️ KURT YAPI MERKEZ")
st.subheader("Personel İzin Yönetim Sistemi")

tab1, tab2, tab3 = st.tabs(["📲 Talep Ekranı", "⚙️ Yönetici Onay", "📊 Bakiye Paneli"])

with tab1:
    with st.form("izin_formu"):
        ad = st.text_input("Ad Soyad")
        izin_turu = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Hastalık/Rapor"])
        baslangic = st.date_input("Başlangıç Tarihi")
        bitis = st.date_input("Bitiş Tarihi")
        if st.form_submit_button("Talebi Gönder"):
            if ad:
                gun_sayisi = (bitis - baslangic).days + 1
                islem_id = datetime.now().strftime("%Y%m%d%H%M%S")
                tarih_str = datetime.now().strftime("%d-%m-%Y")
                ws_talepler.append_row([islem_id, tarih_str, ad, izin_turu, str(baslangic), str(bitis), gun_sayisi, "⏳ Bekliyor"])
                st.success("Talebiniz başarıyla alındı. Yönetici onayını bekliyor.")
            else:
                st.error("Lütfen Ad Soyad giriniz.")

with tab2:
    if st.text_input("Yönetici Şifresi (PIN):", type="password") == "1923":
        if not df_talepler.empty:
            bekleyenler = df_talepler[df_talepler['Durum'] == '⏳ Bekliyor']
            st.dataframe(df_talepler)
            if not bekleyenler.empty:
                onaylanacak_id = st.selectbox("İşlem yapılacak talep ID:", bekleyenler['ID'].tolist())
                if st.button("✅ Onayla"):
                    hucre = ws_talepler.find(str(onaylanacak_id))
                    ws_talepler.update_cell(hucre.row, 8, "✅ Onaylandı")
                    st.success("Talep Onaylandı! Sayfayı yenileyin.")
                if st.button("❌ Reddet"):
                    hucre = ws_talepler.find(str(onaylanacak_id))
                    ws_talepler.update_cell(hucre.row, 8, "❌ Reddedildi")
                    st.error("Talep Reddedildi!")

with tab3:
    st.dataframe(df_bakiyeler, use_container_width=True)
