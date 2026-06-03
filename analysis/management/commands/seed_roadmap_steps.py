"""
Management command: seed_roadmap_steps

Har bir standart uchun tayyor roadmap qadamlarini yuklaydi.
Bu qadamlar gap-analiz natijasida foydalanuvchiga ko'rsatiladi.
AI bu qadamlarni ixtiro qilmaydi — bazadan oladi.

    python manage.py seed_roadmap_steps
    python manage.py seed_roadmap_steps --standard iso9001
"""
from django.core.management.base import BaseCommand
from analysis.models import Standard, StandardRoadmapStep


# ─── ISO 9001 — Sifat menejmenti tizimi ──────────────────────────────────────
STEPS_9001 = [
    (
        1, "Hozirgi holat tahlili (GAP analiz)",
        "Korxonaning ISO 9001 talablariga mos kelmaydigan joylari aniqlanadi. "
        "Mavjud jarayonlar, hujjatlar va tartiblar ko'rib chiqiladi. "
        "Kamchiliklar ro'yxati tuziladi va tuzatish yo'llari belgilanadi.",
        ["GAP analiz hisoboti", "Kamchiliklar ro'yxati", "Tuzatish rejasi"],
        14,
    ),
    (
        2, "QMS doirasi va siyosat ishlab chiqish",
        "Sifat menejmenti tizimining doirasi (scope) aniqlanadi. "
        "Sifat siyosati hujjatlashtiriladi va rahbariyat tomonidan tasdiqlanadi. "
        "Tashkilot konteksti, manfaatdor tomonlar va ularning talablari ro'yxati tuziladi.",
        ["Sifat siyosati hujjati", "QMS doirasi (scope)", "Manfaatdor tomonlar ro'yxati"],
        10,
    ),
    (
        3, "Jarayonlar xaritasi va tartiblar",
        "Asosiy biznes jarayonlari aniqlanadi va xaritalanadi. "
        "Har jarayon uchun protseduralar va ko'rsatmalar yoziladi. "
        "Jarayonlar o'zaro bog'liqligi belgilanadi, mas'ullar tayinlanadi.",
        ["Jarayonlar xaritasi", "Protseduralar to'plami", "Mas'uliyat matritsasi (RACI)"],
        21,
    ),
    (
        4, "Risk va imkoniyatlarni baholash",
        "Tashkilotning asosiy risklari aniqlanadi va baholanadi. "
        "Har risk uchun oldini olish yoki minimallash choralari belgilanadi. "
        "Imkoniyatlar ro'yxati tuziladi va ulardan foydalanish rejasi ishlab chiqiladi.",
        ["Risk va imkoniyatlar registri", "Risk baholash uslubiyati", "Muolaja rejalari"],
        14,
    ),
    (
        5, "Xodimlar o'qitish va malaka oshirish",
        "ISO 9001 talablari bo'yicha xodimlarga o'quv mashg'ulotlari o'tkaziladi. "
        "Har xodimning vazifalari va malaka talablari aniqlanadi, hujjatlanadi. "
        "O'qitish natijalari baholanadi va tasdiqlash imtihoni o'tkaziladi.",
        ["O'qitish rejasi", "Malaka matritsasi", "O'qitish natijalari bayonnomasi"],
        7,
    ),
    (
        6, "Ichki audit o'tkazish",
        "Ichki auditorlar tayyorlanadi yoki tashqaridan yollanadi. "
        "Audit rejasi tuziladi va barcha bo'limlar tekshiriladi. "
        "Nomuvofiqliklar qayd etiladi, tuzatuvchi choralar belgilanadi.",
        ["Ichki audit rejasi", "Audit protokoli", "Nomuvofiqliklar ro'yxati", "Tuzatuvchi choralar rejasi"],
        14,
    ),
    (
        7, "Rahbariyat sharhi (Management Review)",
        "Rahbariyat QMS samaradorligini ko'rib chiqadi. "
        "Audit natijalari, mijoz shikoyatlari, KPI ko'rsatkichlari tahlil qilinadi. "
        "Tizimni yaxshilash bo'yicha qarorlar qabul qilinadi va hujjatlanadi.",
        ["Rahbariyat sharhi bayonnomasi", "KPI ko'rsatkichlari hisoboti", "Yaxshilash rejalari"],
        7,
    ),
    (
        8, "Sertifikatlash auditi tayyorgarligi",
        "Sertifikatlash organi tanlanadi va shartnoma tuziladi. "
        "Barcha hujjatlar va yozuvlar sertifikatlash talablariga mosligi tekshiriladi. "
        "Pre-audit o'tkaziladi, kamchiliklar bartaraf etiladi.",
        ["To'liq hujjatlar to'plami", "Pre-audit natijalari", "Sertifikatlash shartnomasi"],
        14,
    ),
]

# ─── ISO 14001 — Atrof-muhit menejmenti tizimi ───────────────────────────────
STEPS_14001 = [
    (
        1, "Ekologik holat tahlili",
        "Korxonaning atrof-muhitga ta'siri o'rganiladi. "
        "Muhim ekologik aspektlar aniqlanadi (chiqindilar, emissiyalar, suv iste'moli). "
        "Amaldagi qonuniy ekologik talablar ro'yxati tuziladi.",
        ["Ekologik holat tahlili hisoboti", "Aspektlar va ta'sirlar ro'yxati", "Qonuniy talablar registri"],
        14,
    ),
    (
        2, "Atrof-muhit siyosati va maqsadlar",
        "Atrof-muhit siyosati hujjatlashtiriladi va rahbariyat tasdiqlaydi. "
        "O'lchanaladigan ekologik maqsadlar belgilanadi. "
        "Maqsadlarga erishish dasturlari va mas'ullar tayinlanadi.",
        ["Atrof-muhit siyosati", "Ekologik maqsadlar va dasturlar", "Mas'uliyat taqsimoti"],
        10,
    ),
    (
        3, "Operatsion nazorat joriy etish",
        "Muhim ekologik aspektlar nazorat ostiga olinadi. "
        "Chiqindilarni saralash, ko'k va xavfli chiqindilar bo'yicha tartiblar joriy etiladi. "
        "Ifloslanishning oldini olish choralari ko'riladi.",
        ["Operatsion nazorat protsedurasi", "Chiqindilarni boshqarish tartibi", "Monitoring jadvali"],
        21,
    ),
    (
        4, "Favqulodda ekologik vaziyat rejasi",
        "Ekologik falokatlar (to'kilmalar, yong'in, ifloslanish) stsenariylari aniqlanadi. "
        "Har stsenariy uchun javob berish tartibi yoziladi va mashqlar o'tkaziladi. "
        "Favqulodda aloqa yo'nalishi belgilanadi.",
        ["Favqulodda vaziyat rejasi", "Mashq bayonnomasi", "Aloqa ro'yxati"],
        7,
    ),
    (
        5, "Monitoring va o'lchash tizimi",
        "Asosiy ekologik ko'rsatkichlar (emissiya, suv, elektr) uchun monitoring o'rnatiladi. "
        "O'lchov uskunalari kalibrlash takvimi tuziladi. "
        "Monitoring natijalari qayd etish shakllari tayyorlanadi.",
        ["Monitoring rejasi", "Kalibrlash takvimi", "Qayd etish shakllari"],
        14,
    ),
    (
        6, "Ichki audit va rahbariyat sharhi",
        "EMS ichki auditi o'tkaziladi, nomuvofiqliklar aniqlanadi. "
        "Rahbariyat ekologik samaradorlikni ko'rib chiqadi. "
        "Tuzatuvchi choralar belgilanadi va bajarilishi kuzatiladi.",
        ["Ichki audit hisoboti", "Rahbariyat sharhi bayonnomasi", "Tuzatuvchi choralar"],
        14,
    ),
    (
        7, "Sertifikatlash auditi",
        "Sertifikatlash organi bilan shartnoma tuziladi. "
        "1-bosqich (hujjatlar) va 2-bosqich (saytda audit) o'tkaziladi. "
        "Aniqlangan kamchiliklar bartaraf etiladi, sertifikat olinadi.",
        ["Sertifikatlash shartnomasi", "Audit natijalari", "ISO 14001 sertifikati"],
        14,
    ),
]

# ─── ISO 45001 — Mehnat xavfsizligi va sog'liqni saqlash ─────────────────────
STEPS_45001 = [
    (
        1, "Xavf-xatarlar tahlili",
        "Barcha ish joylari va jarayonlardagi xavf-xatarlar aniqlanadi. "
        "Har xavf uchun risk darajasi baholanadi (ehtimollik × oqibat). "
        "Mavjud nazorat vositalari samaradorligi tekshiriladi.",
        ["Xavf-xatarlar registri", "Risk baholash uslubiyati", "Nazorat choralari ro'yxati"],
        14,
    ),
    (
        2, "OH&S siyosati va maqsadlar",
        "Mehnat xavfsizligi siyosati hujjatlashtiriladi va rahbariyat tasdiqlaydi. "
        "O'lchanaladigan xavfsizlik maqsadlari belgilanadi (LTIFR, TRIR). "
        "Mas'ullar tayinlanadi, dasturlar ishlab chiqiladi.",
        ["OH&S siyosati", "Xavfsizlik maqsadlari", "Amaliy dasturlar"],
        10,
    ),
    (
        3, "Shaxsiy himoya vositalari (PPE) tizimi",
        "Har ish turi uchun zarur PPE aniqlanadi va ta'minlanadi. "
        "PPE berib-qaytarish tizimi joriy etiladi, hisobga olish yo'lga qo'yiladi. "
        "Xodimlar PPE to'g'ri ishlatilishi bo'yicha o'qitiladi.",
        ["PPE matritsasi", "PPE berish-qaytarish jurnali", "O'qitish bayonnomasi"],
        7,
    ),
    (
        4, "Xodimlar o'qitish va ishtiroki",
        "Barcha xodimlar mehnat xavfsizligi bo'yicha o'qitiladi. "
        "Xodimlar xavf-xatarlarni aniqlash va hisobot berish tizimiga jalb qilinadi. "
        "Xavfsizlik qo'mitasi tuziladi (agar talab etilsa).",
        ["O'qitish dasturi", "O'qitish bayonnomalari", "Xavfsizlik qo'mitasi nizomi"],
        14,
    ),
    (
        5, "Baxtsiz hodisa tahlili va hisobot tizimi",
        "Baxtsiz hodisalar, deyarli hodisalar (near miss) hisobot shakli tayyorlanadi. "
        "Hodisalarni tekshirish tartibi joriy etiladi (ildiz sabab tahlili). "
        "Profilaktika choralari kuzatiladi va samaradorligi baholanadi.",
        ["Hodisa hisobot shakli", "Tekshiruv tartibi", "Profilaktika choralari ro'yxati"],
        14,
    ),
    (
        6, "Favqulodda vaziyat rejasi va mashqlar",
        "Mehnat xavfsizligi bilan bog'liq favqulodda stsenariylar ishlab chiqiladi. "
        "Evakuatsiya rejasi va avariya signalizatsiyasi tekshiriladi. "
        "Yillik mashqlar o'tkaziladi va natijalari hujjatlanadi.",
        ["Favqulodda vaziyat rejasi", "Evakuatsiya sxemasi", "Mashq bayonnomasi"],
        7,
    ),
    (
        7, "Ichki audit va sertifikatlash",
        "OH&S ichki auditi o'tkaziladi, nomuvofiqliklar bartaraf etiladi. "
        "Rahbariyat sharhi o'tkaziladi, tizim samaradorligi baholanadi. "
        "Sertifikatlash auditi o'tkaziladi, ISO 45001 sertifikati olinadi.",
        ["Ichki audit hisoboti", "Rahbariyat sharhi", "ISO 45001 sertifikati"],
        14,
    ),
]

# ─── ISO 22000 — Oziq-ovqat xavfsizligi ──────────────────────────────────────
STEPS_22000 = [
    (
        1, "Dastlabki tahlil va PRP baholash",
        "Oziq-ovqat xavfsizligi tizimining hozirgi holati tahlil qilinadi. "
        "Dastlabki shartli dasturlar (PRPs) baholanadi: gigiena, sanitariya, zararkunanda nazorat. "
        "Kamchiliklar ro'yxati tuziladi.",
        ["Dastlabki tahlil hisoboti", "PRP baholash natijalari", "Kamchiliklar ro'yxati"],
        14,
    ),
    (
        2, "Oziq-ovqat xavfsizligi guruhini tuzish",
        "HACCP/FSMS guruhi tashkil etiladi, rahbar tayinlanadi. "
        "Guruh a'zolari vazifalari va mas'uliyati belgilanadi. "
        "Guruh HACCP va ISO 22000 bo'yicha o'qitiladi.",
        ["Guruh tarkibi buyrug'i", "Mas'uliyat taqsimoti", "O'qitish bayonnomasi"],
        7,
    ),
    (
        3, "Mahsulot tavsifi va xavf tahlili",
        "Barcha mahsulotlar tavsiflanadi (tarkib, qadoqlash, saqlash, iste'molchi). "
        "Ishlab chiqarish oqim diagrammasi tuziladi va tasdiqlandi. "
        "Har qadamda biologik, kimyoviy, fizik xavflar tahlil qilinadi.",
        ["Mahsulot tavsifi varaqalari", "Oqim diagrammasi", "Xavf tahlili jadvali"],
        21,
    ),
    (
        4, "CCP va OPRP aniqlash",
        "Muhim nazorat nuqtalari (CCP) aniqlanadi (pishirish harorati, metal detektor va h.k.). "
        "Har CCP uchun kritik chegaralar, monitoring tartibi va tuzatuvchi choralar belgilanadi. "
        "Operatsion PRPlar (OPRPs) belgilanadi.",
        ["HACCP rejasi", "CCP monitoring jadvali", "Tuzatuvchi choralar tartibi"],
        14,
    ),
    (
        5, "Kuzatuvchanlik (Traceability) tizimi",
        "Xomashyodan tayyor mahsulotgacha kuzatuvchanlik tizimi joriy etiladi. "
        "Partiya raqamlash tizimi o'rnatiladi. "
        "Qaytarib olish (recall) mashqi o'tkaziladi (4 soat ichida 100% top).",
        ["Kuzatuvchanlik tartibi", "Partiya raqamlash qoidasi", "Recall mashq bayonnomasi"],
        14,
    ),
    (
        6, "Validatsiya va tekshiruv",
        "HACCP rejasi validatsiya qilinadi (nazariy va amaliy). "
        "Monitoring usullari tasdiqlangan metod bilan tekshiriladi. "
        "Ichki FSMS auditi o'tkaziladi.",
        ["Validatsiya hisoboti", "Tekshiruv natijalari", "Ichki audit hisoboti"],
        14,
    ),
    (
        7, "Sertifikatlash auditi",
        "ISO 22000 yoki FSSC 22000 sertifikatlash organi tanlanadi. "
        "1-bosqich va 2-bosqich auditlari o'tkaziladi. "
        "Kamchiliklar bartaraf etiladi, sertifikat olinadi.",
        ["Sertifikatlash shartnomasi", "Audit natijalari", "ISO 22000 sertifikati"],
        14,
    ),
]

# ─── ISO/IEC 27001 — Axborot xavfsizligi ─────────────────────────────────────
STEPS_27001 = [
    (
        1, "ISMS doirasi va aktiv inventarizatsiya",
        "Axborot xavfsizligi menejmenti tizimi doirasi aniqlanadi. "
        "Barcha axborot aktivlari (serverlar, dasturlar, ma'lumotlar) inventarizatsiya qilinadi. "
        "Har aktivning qiymati va muhimligi baholanadi.",
        ["ISMS doirasi hujjati", "Aktivlar inventari", "Aktivlar qiymati matritsasi"],
        14,
    ),
    (
        2, "Risk baholash va muolaja",
        "Axborot xavfsizligi risklari aniqlanadi va baholanadi. "
        "Qabul qilinmaydigan risklar uchun muolaja rejalari ishlab chiqiladi. "
        "Risk qabul qilish mezonlari belgilanadi va rahbariyat tasdiqlaydi.",
        ["Risk baholash metodologiyasi", "Risk registri", "Risk muolaja rejasi"],
        21,
    ),
    (
        3, "Axborot xavfsizligi siyosati va tartiblar",
        "Axborot xavfsizligi siyosati hujjatlashtiriladi. "
        "Kirish huquqlari boshqaruvi, parol siyosati, shifrlash tartiblari yoziladi. "
        "Xodimlar AX bo'yicha o'qitish o'tkaziladi.",
        ["AX siyosati", "Kirish nazorati tartibi", "O'qitish dasturi"],
        21,
    ),
    (
        4, "Texnik nazorat vositalarini joriy etish",
        "Firewall, antivirus, IDS/IPS tizimlar sozlanadi. "
        "Ma'lumotlarni zaxiralash (backup) tizimi joriy etiladi. "
        "Tizimlar monitoringi va jurnal yuritish yo'lga qo'yiladi.",
        ["Texnik nazorat ro'yxati", "Zaxiralash tartibi", "Monitoring qoidasi"],
        21,
    ),
    (
        5, "Hodisalarga javob berish rejasi",
        "Axborot xavfsizligi hodisalarini aniqlash va hisobot berish tartibi joriy etiladi. "
        "Hodisalarga javob berish komandasi tashkil etiladi. "
        "Hodisa simulyatsiyasi o'tkaziladi.",
        ["Hodisalarga javob rejasi", "Komanda tarkibi", "Simulyatsiya bayonnomasi"],
        14,
    ),
    (
        6, "Ichki audit va sertifikatlash",
        "ISMS ichki auditi o'tkaziladi. "
        "Rahbariyat sharhi o'tkaziladi. "
        "ISO/IEC 27001 sertifikatlash auditi o'tkaziladi.",
        ["Ichki audit hisoboti", "Rahbariyat sharhi", "ISO 27001 sertifikati"],
        14,
    ),
]

# ─── ISO 50001 — Energiya menejmenti ─────────────────────────────────────────
STEPS_50001 = [
    (
        1, "Energiya ko'rib chiqish (Energy Review)",
        "Barcha energiya manbalari va iste'molchilar aniqlanadi. "
        "Asosiy energiya foydalanish sohalari (SEU) aniqlanadi. "
        "Energiya bazaviy ko'rsatkichi (EnB) o'rnatiladi.",
        ["Energiya ko'rib chiqish hisoboti", "SEU ro'yxati", "EnB hisob-kitob"],
        14,
    ),
    (
        2, "Energiya siyosati va maqsadlar",
        "Energiya siyosati hujjatlashtiriladi. "
        "O'lchanaladigan energiya maqsadlari belgilanadi (kWh/mahsulot birligi). "
        "Energiya samaradorligi ko'rsatkichlari (EnPI) o'rnatiladi.",
        ["Energiya siyosati", "EnPI va maqsadlar", "Harakatlar rejasi"],
        10,
    ),
    (
        3, "Monitoring va o'lchash",
        "Asosiy SEUlar uchun o'lchov hisoblagichlari o'rnatiladi. "
        "Energiya ma'lumotlarini yig'ish tizimi joriy etiladi. "
        "Tahlil va hisobot shakllari tayyorlanadi.",
        ["Monitoring rejasi", "O'lchov hisoblagichlari ro'yxati", "Hisobot shakllari"],
        14,
    ),
    (
        4, "Xodimlar o'qitish va energiya madaniyati",
        "Xodimlar energiya tejash bo'yicha o'qitiladi. "
        "Energiya tejash g'oyalari uchun tizim joriy etiladi. "
        "Energiya maqsadlari xodimlarga yetkaziladi.",
        ["O'qitish dasturi", "G'oyalar tizimi", "Komunikatsiya rejasi"],
        7,
    ),
    (
        5, "Ichki audit va sertifikatlash",
        "EnMS ichki auditi o'tkaziladi. "
        "Rahbariyat energiya ko'rsatkichlarini ko'rib chiqadi. "
        "ISO 50001 sertifikatlash auditi o'tkaziladi.",
        ["Ichki audit hisoboti", "Rahbariyat sharhi", "ISO 50001 sertifikati"],
        14,
    ),
]

# ─── ISO 13485 — Tibbiy qurilmalar ───────────────────────────────────────────
STEPS_13485 = [
    (
        1, "Regulatory talablar tahlili",
        "Mahsulot uchun tegishli regulatory talablar aniqlanadi (FDA, MDR, TGA). "
        "Klassifikatsiya belgilanadi. "
        "QMS doirasi va mahsulot ro'yxati tuziladi.",
        ["Regulatory talablar ro'yxati", "Mahsulot klassifikatsiyasi", "QMS doirasi"],
        14,
    ),
    (
        2, "Dizayn va ishlab chiqish nazorati",
        "Design & development tartibi yoziladi (kirisH, chiqish, tekshiruv, validatsiya). "
        "Klinik baholash (clinical evaluation) tartibi joriy etiladi. "
        "Dizayn tarixi fayli (Design History File) tuziladi.",
        ["Design controls tartibi", "Design History File", "Klinik baholash tartibi"],
        21,
    ),
    (
        3, "Kuzatuvchanlik va sterilizatsiya",
        "Mahsulotlar uchun UDI (yagona qurilma identifikatori) tizimi joriy etiladi. "
        "Steril mahsulotlar uchun validatsiya o'tkaziladi. "
        "Kuzatuvchanlik (traceability) tizimi o'rnatiladi.",
        ["Kuzatuvchanlik tartibi", "Sterilizatsiya validatsiya hisoboti", "UDI tizimi"],
        21,
    ),
    (
        4, "Baxtsiz hodisa hisobot tizimi (Vigilance)",
        "Post-market surveillance tizimi joriy etiladi. "
        "Baxtsiz hodisalar va FSCA hisobot tartibi yoziladi. "
        "Qaytarib olish (recall) tartibi joriy etiladi.",
        ["Vigilance tartibi", "FSCA hisobot shakli", "Recall tartibi"],
        14,
    ),
    (
        5, "Ichki audit va sertifikatlash",
        "ISO 13485 ichki auditi o'tkaziladi. "
        "Rahbariyat sharhi o'tkaziladi. "
        "Notified Body auditi o'tkaziladi, sertifikat olinadi.",
        ["Ichki audit hisoboti", "Rahbariyat sharhi", "ISO 13485 sertifikati"],
        14,
    ),
]

# ─── ISO/IEC 17025 — Laboratoriya ────────────────────────────────────────────
STEPS_17025 = [
    (
        1, "Laboratoriya holat tahlili",
        "ISO/IEC 17025 talablariga mos kelmaydigan joylar aniqlanadi. "
        "Kompetentlik talablari, uskunalar va usullar ko'rib chiqiladi. "
        "Kamchiliklar ro'yxati tuziladi.",
        ["Laboratoriya holat tahlili", "Kompetentlik matritsasi", "Kamchiliklar ro'yxati"],
        10,
    ),
    (
        2, "Usul validatsiyasi va kalibrlash",
        "Sinov va kalibrlash usullari validatsiya qilinadi. "
        "O'lchov aniqlik darajasi (measurement uncertainty) hisoblanadi. "
        "Uskunalar kalibrlash takvimi tuziladi va amalga oshiriladi.",
        ["Validatsiya hisobotlari", "Measurement uncertainty hisobi", "Kalibrlash takvimi"],
        21,
    ),
    (
        3, "Sifat menejmenti tizimi hujjatlari",
        "Laboratoriya QMS hujjatlari tuziladi (sifat qo'llanmasi, tartiblar). "
        "Noaniqlik, kuzatuvchanlik, noto'g'ri natijalar tartiblari yoziladi. "
        "Hujjatlar nazorat tizimi joriy etiladi.",
        ["Sifat qo'llanmasi", "Tartiblar to'plami", "Hujjatlar nazorat reestri"],
        14,
    ),
    (
        4, "Proficiency Testing (PT) ishtiroki",
        "Tegishli PT provayderlar aniqlanadi, ishtiroki rejalashtiriladi. "
        "PT natijalari tahlil qilinadi va qabul qilish mezonlari belgilanadi. "
        "Qoniqarsiz natijalar uchun tuzatuvchi choralar ko'riladi.",
        ["PT ishtiroki jadvali", "PT natijalari tahlili", "Tuzatuvchi choralar"],
        14,
    ),
    (
        5, "Akkreditatsiya auditi",
        "Akkreditatsiya organi tanlanadi (UZAK, ILAC a'zolari). "
        "Pre-akkreditatsiya tekshiruvi o'tkaziladi. "
        "Akkreditatsiya auditi o'tkaziladi, amal qilish ko'lami (scope) tasdiqlanadi.",
        ["Akkreditatsiya arizasi", "Pre-audit natijalari", "Akkreditatsiya sertifikati"],
        14,
    ),
]


# ─── Kalit → qadamlar xaritasi ───────────────────────────────────────────────
STEPS_MAP = {
    '9001':  STEPS_9001,
    '14001': STEPS_14001,
    '45001': STEPS_45001,
    '22000': STEPS_22000,
    '27001': STEPS_27001,
    '50001': STEPS_50001,
    '13485': STEPS_13485,
    '17025': STEPS_17025,
}


class Command(BaseCommand):
    help = 'Standartlar uchun roadmap qadamlarini yuklaydi (bazadan, AI tegmaydi)'

    def add_arguments(self, parser):
        parser.add_argument('--standard', default='all',
                            help='Qaysi standart: 9001|14001|45001|22000|27001|50001|13485|17025|all')
        parser.add_argument('--reset', action='store_true',
                            help='Qayta yaratish (mavjudlarni o\'chirib)')

    def handle(self, *args, **options):
        target = options['standard']
        total_created = 0
        total_updated = 0

        for key, steps_list in STEPS_MAP.items():
            if target != 'all' and target != key:
                continue

            standards = Standard.objects.filter(code__icontains=key, is_active=True)
            if not standards.exists():
                self.stdout.write(self.style.WARNING(f'  {key} standarti topilmadi'))
                continue

            for std in standards:
                if options['reset']:
                    StandardRoadmapStep.objects.filter(standard=std).delete()

                self.stdout.write(f'\n  {std.code}:')
                created = 0
                updated = 0

                for order, title, description, deliverables, duration_days in steps_list:
                    obj, was_created = StandardRoadmapStep.objects.get_or_create(
                        standard=std,
                        order=order,
                        defaults={
                            'title': title,
                            'description': description,
                            'deliverables': deliverables,
                            'duration_days': duration_days,
                            'is_active': True,
                        },
                    )
                    if was_created:
                        created += 1
                        total_created += 1
                    else:
                        changed = False
                        if obj.title != title:
                            obj.title = title
                            changed = True
                        if obj.description != description:
                            obj.description = description
                            changed = True
                        if obj.deliverables != deliverables:
                            obj.deliverables = deliverables
                            changed = True
                        if obj.duration_days != duration_days:
                            obj.duration_days = duration_days
                            changed = True
                        if changed:
                            obj.save()
                            updated += 1
                            total_updated += 1

                self.stdout.write(
                    f'    {created} yangi qadam, {updated} yangilandi, '
                    f'{len(steps_list) - created - updated} mavjud'
                )

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Jami: {total_created} yangi, {total_updated} yangilandi.'
        ))
