from django.core.management.base import BaseCommand
from analysis.models import Standard, Question


# Har bir standart uchun gap-analiz savollari (UZ matn + qisqacha klaus izohi).
QUESTIONS = {
    '9001': [
        ('Sizda sifat siyosati hujjatlashtirilganmi?', 'Quality policy'),
        ('Rahbariyat sifat tizimiga mas\'ulmi?', 'Leadership'),
        ('Xodimlar malakasi baholanadi va hujjatlashtiriladimi?', 'Competence'),
        ('Ichki auditlar muntazam o\'tkaziladimi?', 'Internal audit'),
        ('Nomuvofiqliklar qayd etiladi va tuzatiladimi?', 'Nonconformity'),
        ('Hujjatlar nazorati tizimi bormi?', 'Document control'),
        ('Mijoz qoniqishi o\'lchanadi va tahlil qilinadimi?', 'Customer satisfaction'),
        ('Korrektiv choralar qo\'llaniladimi?', 'Corrective actions'),
        ('Jarayonlar aniqlangan va o\'zaro bog\'liqligi belgilanganmi?', 'Process approach'),
        ('Risk va imkoniyatlar baholanadimi?', 'Risk-based thinking'),
        ('Rahbariyat tahlili (management review) o\'tkaziladimi?', 'Management review'),
        ('Yetkazib beruvchilar baholanadi va nazorat qilinadimi?', 'Supplier control'),
    ],
    '22000': [
        ('Oziq-ovqat xavfsizligi siyosati hujjatlashtirilganmi?', 'Food safety policy'),
        ('HACCP rejasi ishlab chiqilganmi?', 'HACCP plan'),
        ('Muhim nazorat nuqtalari (CCP) aniqlanganmi?', 'Critical Control Points'),
        ('Old shart dasturlari (PRP) joriy etilganmi?', 'Prerequisite programmes'),
        ('Xavf tahlili (hazard analysis) o\'tkazilganmi?', 'Hazard analysis'),
        ('Mahsulot kuzatuvchanligi (traceability) tizimi bormi?', 'Traceability'),
        ('Qaytarib olish (recall) protsedurasi mavjudmi?', 'Recall procedure'),
        ('Gigiyena va sanitariya talablari bajariladimi?', 'Hygiene & sanitation'),
        ('Allergenlar nazorat qilinadimi?', 'Allergen control'),
        ('Xodimlarning oziq-ovqat xavfsizligi bo\'yicha trening bormi?', 'Training'),
        ('Monitoring va o\'lchov natijalari qayd etiladimi?', 'Monitoring'),
        ('Tashqi va ichki aloqa (communication) tizimi bormi?', 'Communication'),
    ],
    '14001': [
        ('Atrof-muhit siyosati hujjatlashtirilganmi?', 'Environmental policy'),
        ('Ekologik aspektlar (environmental aspects) aniqlanganmi?', 'Environmental aspects'),
        ('Qonuniy va boshqa talablar ro\'yxati yuritiladimi?', 'Legal requirements'),
        ('Ekologik maqsadlar va dasturlar belgilanganmi?', 'Objectives'),
        ('Chiqindilar boshqaruvi tizimi bormi?', 'Waste management'),
        ('Energiya va resurs iste\'moli nazorat qilinadimi?', 'Resource use'),
        ('Favqulodda vaziyatlarga tayyorgarlik rejasi bormi?', 'Emergency preparedness'),
        ('Ekologik ko\'rsatkichlar monitoring qilinadimi?', 'Monitoring'),
        ('Xodimlar ekologik mas\'uliyat bo\'yicha o\'qitiladimi?', 'Competence & awareness'),
        ('Ichki ekologik auditlar o\'tkaziladimi?', 'Internal audit'),
        ('Ifloslanishning oldini olish choralari bormi?', 'Pollution prevention'),
        ('Rahbariyat tahlili o\'tkaziladimi?', 'Management review'),
    ],
    '45001': [
        ('Mehnat xavfsizligi siyosati hujjatlashtirilganmi?', 'OH&S policy'),
        ('Xavf-xatarlar aniqlanadi va baholanadimi?', 'Hazard identification'),
        ('Risklarni baholash (risk assessment) o\'tkaziladimi?', 'Risk assessment'),
        ('Xodimlar maslahatlashuvi va ishtiroki ta\'minlanadimi?', 'Worker participation'),
        ('Shaxsiy himoya vositalari (PPE) ta\'minlanadimi?', 'PPE'),
        ('Baxtsiz hodisalar qayd etiladi va tekshiriladimi?', 'Incident investigation'),
        ('Favqulodda vaziyatlar rejasi mavjudmi?', 'Emergency preparedness'),
        ('Xavfsizlik bo\'yicha treninglar o\'tkaziladimi?', 'Training'),
        ('Sog\'liq monitoringi (health surveillance) bormi?', 'Health surveillance'),
        ('Qonuniy mehnat muhofazasi talablari bajariladimi?', 'Legal compliance'),
        ('Ichki MMX auditlari o\'tkaziladimi?', 'Internal audit'),
        ('Rahbariyat tahlili o\'tkaziladimi?', 'Management review'),
    ],
}


class Command(BaseCommand):
    help = 'Barcha ISO standartlari (9001/22000/14001/45001) uchun gap-analiz savollarini yuklaydi'

    def handle(self, *args, **options):
        total = 0
        for code_key, questions in QUESTIONS.items():
            standards = Standard.objects.filter(code__icontains=code_key, type='international')
            if not standards.exists():
                self.stdout.write(self.style.WARNING(f'ISO {code_key} standarti topilmadi — o\'tkazib yuborildi'))
                continue
            for standard in standards:
                for i, (text, help_text) in enumerate(questions):
                    _, created = Question.objects.get_or_create(
                        standard=standard,
                        text=text,
                        defaults={'help_text': help_text, 'order': i, 'answer_type': 'yes_partial_no'},
                    )
                    if created:
                        total += 1
                self.stdout.write(f'  {standard.code}: {len(questions)} savol tekshirildi')
        self.stdout.write(self.style.SUCCESS(f'{total} ta yangi savol yuklandi.'))
