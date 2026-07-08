import streamlit as st
import pandas as pd
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
import gspread
from google.oauth2.service_account import Credentials
import json

# --- E-POSTA AYARLARI ---
GONDERICI_MAIL = "meltempolat@kurtyapihafriyat.com.tr" 
UYGULAMA_SIFRESI = "iqiubhtmgdcfjnut"
ALICI_MAIL = "ik@kurtyapihafriyat.com.tr" 

def mail_gonder(ad, izin_turu, baslangic, bitis):
    mesaj = f"Kurt Yapı Merkez'den Yeni İzin Talebi Var!\n\nPersonel: {ad}\nİzin Türü: {izin_turu}\nTarihler: {baslangic} - {bitis}\n\nLütfen sisteme girerek onaylayınız."
    msg = MIMEText(mesaj)
    msg['Subject'] = f'YENİ İZİN TALEBİ: {ad}'
    msg['From'] = GONDERICI_MAIL
    msg['To'] = ALICI_MAIL
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GONDERICI_MAIL, UYGULAMA_SIFRESI)
        server.sendmail(GONDERICI_MAIL, ALICI_MAIL, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

# Sayfa Ayarları
st.set_page_config(page_title="Kurt Yapı İK", page_icon="🏗️", layout="centered")

# --- GOOGLE SHEETS BAĞLANTISI ---
@st.cache_resource
def get_google_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_str = st.secrets["GOOGLE_CREDENTIALS"]
    
    # HATA ÇÖZÜMÜ BURADA: strict=False komutu ile Not Defteri'nin bozduğu karakterleri yoksayıyoruz!
    creds_dict = json.loads(creds_str, strict=False)
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("KurtYapi_IK_Merkez")

# Veritabanına Bağlan
try:
    sh = get_google_sheet()
    ws_talepler = sh.worksheet("Talepler")
    ws_bakiyeler = sh.worksheet("Bakiyeler")
    
    # Excel bomboşsa ilk satıra başlıkları otomatik yazar
    if len(ws_talepler.get_all_values()) == 0:
        ws_talepler.append_row(["ID", "Tarih", "Personel Adı", "İzin Türü", "Başlangıç", "Bitiş", "Gün", "Durum"])
    if len(ws_bakiyeler.get_all_values()) == 0:
        ws_bakiyeler.append_row(["Personel Adı", "Toplam İzin Hakkı", "Kullanılan", "Kalan Bakiye"])
except Exception as e:
    st.error(f"Veri tabanına bağlanılamadı. Hata: {e}")
    st.stop()

# Excel'den Verileri Çek
veri_talepler = ws_talepler.get_all_records()
veri_bakiyeler = ws_bakiyeler.get_all_records()

df_talepler = pd.DataFrame(veri_talepler)
df_bakiyeler = pd.DataFrame(veri_bakiyeler)

st.title("🏗️ KURT YAPI MERKEZ")
st.subheader("Personel İzin Yönetim Sistemi")

# 3 Sekmeli Yapı
tab1, tab2, tab3 = st.tabs(["📲 Talep Ekranı", "⚙️ Yönetici Onay", "📊 Bakiye Paneli"])

# --- 1. SEKME: PERSONEL TALEBİ ---
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
                gun_sayisi = (bitis - baslangic).days + 1
                if gun_sayisi <= 0:
                    st.error("Bitiş tarihi başlangıçtan önce olamaz!")
                else:
                    # Talebi benzersiz bir ID ile kaydet
                    islem_id = datetime.now().strftime("%Y%m%d%H%M%S")
                    tarih_str = datetime.now().strftime("%d-%m-%Y")
                    
                    # Excel 'Talepler' sayfasına yaz
                    ws_talepler.append_row([islem_id, tarih_str, ad, izin_turu, str(baslangic), str(bitis), gun_sayisi, "⏳ Bekliyor"])
                    
                    # Yöneticiye mail at
                    mail_durumu = mail_gonder(ad, izin_turu, baslangic, bitis)
                    if mail_durumu:
                        st.success("Talebiniz başarıyla alındı ve yöneticiye E-Posta gönderildi.")
                    else:
                        st.warning("Talep Excel'e kaydedildi ancak e-posta bildirim motoru çalışmadı.")
            else:
                st.error("Lütfen Ad Soyad giriniz.")

# --- 2. SEKME: YÖNETİCİ ONAYI ---
with tab2:
    st.warning("Bu ekran sadece Onay Yetkilisi tarafından görülür.")
    admin_sifre = st.text_input("Yönetici Şifresini Giriniz (PIN):", type="password")
    
    if admin_sifre == "1923":
        st.success("Yönetici Girişi Başarılı!")
        if not df_talepler.empty:
            bekleyenler = df_talepler[df_talepler['Durum'] == '⏳ Bekliyor']
            st.dataframe(df_talepler)
            
            if not bekleyenler.empty:
                st.divider()
                onaylanacak_id = st.selectbox("İşlem yapılacak talebi (ID) seçin:", bekleyenler['ID'].tolist())
                secilen_talep = bekleyenler[bekleyenler['ID'] == onaylanacak_id].iloc[0]
                st.write(f"**İşlem Yapılan Personel:** {secilen_talep['Personel Adı']} | **Talep Edilen Gün:** {secilen_talep['Gün']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Onayla"):
                        # Talepler sayfasında durumu güncelle
                        hucre = ws_talepler.find(str(onaylanacak_id))
                        ws_talepler.update_cell(hucre.row, 8, "✅ Onaylandı") # 8. Sütun "Durum" sütunudur.
                        
                        # Bakiye düşümü yap
                        personel = secilen_talep['Personel Adı']
                        gun = int(secilen_talep['Gün'])
                        try:
                            # Excel'de personeli bul ve bakiyesini güncelle
                            b_hucre = ws_bakiyeler.find(personel)
                            kullanilan = int(ws_bakiyeler.cell(b_hucre.row, 3).value or 0)
                            yeni_kullanilan = kullanilan + gun
                            toplam = int(ws_bakiyeler.cell(b_hucre.row, 2).value or 0)
                            
                            ws_bakiyeler.update_cell(b_hucre.row, 3, yeni_kullanilan)
                            ws_bakiyeler.update_cell(b_hucre.row, 4, toplam - yeni_kullanilan)
                        except:
                            # Eğer personel listeye ilk defa giriyorsa, varsayılan 14 gün hak ile ekler
                            ws_bakiyeler.append_row([personel, 14, gun, 14-gun])
                            
                        st.success("Talep Onaylandı ve Bakiye Düşüldü! Sayfa yenileniyor...")
                with col2:
                    if st.button("❌ Reddet"):
                        hucre = ws_talepler.find(str(onaylanacak_id))
                        ws_talepler.update_cell(hucre.row, 8, "❌ Reddedildi")
                        st.error("Talep Reddedildi! Sayfa yenileniyor...")
            else:
                st.info("Bekleyen yeni onay talebi bulunmuyor.")
        else:
            st.info("Sistemde henüz talep kaydı yok.")

# --- 3. SEKME: İZİN BAKİYELERİ ---
with tab3:
    st.header("📊 Personel İzin Bakiyeleri")
    st.info("Personellerin hak ettiği toplam izin günlerini arka planda Google Drive'daki 'KurtYapi_IK_Merkez' Excel'inizden değiştirebilirsiniz. Sistem anlık olarak okur.")
    
    if not df_bakiyeler.empty:
        st.dataframe(df_bakiyeler, use_container_width=True)
    else:
        st.warning("Henüz sisteme kaydedilmiş bakiye verisi bulunmuyor.")
