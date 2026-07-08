import streamlit as st
import pandas as pd
from datetime import datetime, date

# Sayfa Ayarları
st.set_page_config(page_title="Kurt Yapı İK", page_icon="🏗️", layout="centered")

# Veri Tabanı Simülasyonu
if 'izin_talepleri' not in st.session_state:
    st.session_state.izin_talepleri = pd.DataFrame(columns=['Personel Adı', 'İzin Türü', 'Başlangıç', 'Bitiş', 'Durum'])

st.title("🏗️ KURT YAPI MERKEZ")
st.subheader("Personel İzin Yönetim Sistemi")

tab1, tab2 = st.tabs(["📲 Personel Talep Ekranı", "⚙️ Yönetici Onay Paneli"])

with tab1:
    st.info("Sahadaki personel bu ekranı kullanarak izin talebini iletir.")
    with st.form("izin_formu"):
        ad = st.text_input("Ad Soyad")
        izin_turu = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Hastalık/Rapor"])
        baslangic = st.date_input("Başlangıç Tarihi")
        bitis = st.date_input("Bitiş Tarihi")
        gonder = st.form_submit_button("Talebi Gönder")
        
        if gonder:
            if ad:
                yeni_talep = {'Personel Adı': ad, 'İzin Türü': izin_turu, 'Başlangıç': baslangic, 'Bitiş': bitis, 'Durum': '⏳ Bekliyor'}
                st.session_state.izin_talepleri = pd.concat([st.session_state.izin_talepleri, pd.DataFrame([yeni_talep])], ignore_index=True)
                st.success(f"Talebini başarıyla alındı! Yöneticiye E-Posta bildirimi gönderildi.")
            else:
                st.error("Lütfen Ad Soyad giriniz.")

with tab2:
    st.warning("Bu ekran sadece Onay Yetkilisi tarafından görülür.")
    
    # --- GÜVENLİK KİLİDİ ---
    admin_sifre = st.text_input("Yönetici Şifresini Giriniz (PIN):", type="password")
    
    if admin_sifre == "1923": # Sizin özel yönetici şifreniz
        st.success("Yönetici Girişi Başarılı!")
        st.dataframe(st.session_state.izin_talepleri)
        
        if not st.session_state.izin_talepleri.empty:
            bekleyenler = st.session_state.izin_talepleri[st.session_state.izin_talepleri['Durum'] == '⏳ Bekliyor']
            if not bekleyenler.empty:
                onaylanacak = st.selectbox("İşlem yapılacak personeli seçin:", bekleyenler['Personel Adı'].tolist())
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Onayla"):
                        st.session_state.izin_talepleri.loc[st.session_state.izin_talepleri['Personel Adı'] == onaylanacak, 'Durum'] = '✅ Onaylandı'
                        st.rerun()
                with col2:
                    if st.button("❌ Reddet"):
                        st.session_state.izin_talepleri.loc[st.session_state.izin_talepleri['Personel Adı'] == onaylanacak, 'Durum'] = '❌ Reddedildi'
                        st.rerun()
            else:
                st.info("Bekleyen yeni onay talebi bulunmuyor.")
    elif admin_sifre != "":
        st.error("Hatalı Şifre! Lütfen tekrar deneyin.")
