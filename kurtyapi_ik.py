def hesapla_izin_hakkı(giris_tarihi_str):
    try:
        giris = pd.to_datetime(giris_tarihi_str).date()
        bugun = date(2026, 7, 8)
        kıdem = bugun.year - giris.year - ((bugun.month, bugun.day) < (giris.month, giris.day))
        
        # Yıllık izin hakkı 1 yıldan sonra başlar
        if kıdem < 1: return 0 
        elif 1 <= kıdem < 5: return 14
        elif 5 <= kıdem < 15: return 20
        else: return 26
    except: return 0
