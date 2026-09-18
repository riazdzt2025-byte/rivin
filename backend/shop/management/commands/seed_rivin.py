from decimal import Decimal
from django.core.management.base import BaseCommand
from shop.models import Category, Product, SiteSetting, DeliveryZone, Coupon

CATS = [
    ("stationery", "স্টেশনারি", "Stationery", "قرطاسية", "✏️"),
    ("cosmetics", "কসমেটিকস", "Cosmetics", "مستحضرات", "🧴"),
    ("toys", "খেলনা", "Toys", "ألعاب", "🧸"),
    ("office", "অফিস", "Office", "مكتب", "🏢"),
    ("art", "আর্ট", "Art", "فن", "🎨"),
    ("school", "স্কুল", "School", "مدرسة", "🎒"),
]
PRODUCTS = [
    ("rivin-0001", "স্টেশনারি", "খাতা A4", "Notebook A4", "دفتر A4", 80, 20, "📓"),
    ("rivin-0002", "স্টেশনারি", "কলম নীল", "Blue Pen", "قلم أزرق", 15, 100, "🖊️"),
    ("rivin-0003", "স্টেশনারি", "পেন্সিল 2B", "Pencil 2B", "قلم رصاص 2B", 10, 100, "✏️"),
    ("rivin-0004", "স্টেশনারি", "রাবার", "Eraser", "ممحاة", 8, 80, "🧽"),
    ("rivin-0005", "স্টেশনারি", "স্কেল 12\"", "Ruler 12\"", "مسطرة 30 سم", 25, 60, "📏"),
    ("rivin-0006", "কসমেটিকস", "ফেস ওয়াশ", "Face Wash", "غسول وجه", 220, 30, "🧴"),
    ("rivin-0007", "কসমেটিকস", "শ্যাম্পু 200ml", "Shampoo 200ml", "شامبو 200 مل", 180, 40, "🧴"),
    ("rivin-0008", "খেলনা", "খেলনা গাড়ি", "Toy Car", "سيارة لعبة", 350, 15, "🚗"),
    ("rivin-0009", "খেলনা", "পুতুল", "Doll", "دمية", 420, 12, "🧸"),
    ("rivin-0010", "খেলনা", "ক্রিকেট বল", "Cricket Ball", "كرة كريكيت", 150, 25, "🏏"),
    ("rivin-0011", "অফিস", "স্ট্যাপলার", "Stapler", "دباسة", 280, 20, "📎"),
    ("rivin-0012", "অফিস", "ফাইল কভার", "File Cover", "غلاف ملف", 35, 80, "📁"),
    ("rivin-0013", "আর্ট", "আর্ট খাতা", "Art Book", "كتاب رسم", 120, 30, "🎨"),
    ("rivin-0014", "আর্ট", "রঙ পেন্সিল 12", "Color Pencil 12", "ألوان 12", 260, 20, "🖍️"),
    ("rivin-0015", "স্কুল", "স্কুল ব্যাগ", "School Bag", "حقيبة مدرسية", 950, 10, "🎒"),
    ("rivin-0016", "স্কুল", "পানির বোতল", "Water Bottle", "قارورة ماء", 250, 30, "🧃"),
    ("rivin-0017", "স্কুল", "টিফিন বক্স", "Tiffin Box", "علبة طعام", 320, 20, "🍱"),
    ("rivin-0018", "স্কুল", "জ্যামিতি বক্স", "Geometry Box", "علبة هندسة", 180, 25, "📐"),
    ("rivin-0019", "অফিস", "ক্যালকুলেটর", "Calculator", "آلة حاسبة", 550, 15, "🧮"),
    ("rivin-0020", "স্টেশনারি", "হাইলাইটার", "Highlighter", "قلم تظليل", 30, 50, "🖍️"),
    ("rivin-0021", "স্টেশনারি", "আঠা স্টিক", "Glue Stick", "صمغ", 25, 60, "🧴"),
    ("rivin-0022", "স্টেশনারি", "কাঁচি", "Scissors", "مقص", 45, 40, "✂️"),
    ("rivin-0023", "কসমেটিকস", "লিপ বাম", "Lip Balm", "مرطب شفاه", 90, 35, "💄"),
    ("rivin-0024", "কসমেটিকস", "পাউডার", "Powder", "بودرة", 140, 30, "🧴"),
]

class Command(BaseCommand):
    help = "Seed RIVIN categories/products (24 demo, idempotent)"
    def handle(self, *args, **opts):
        cat_map = {}
        for code, bn, en, ar, emoji in CATS:
            c, _ = Category.objects.get_or_create(code=code, defaults=dict(name_bn=bn, name_en=en, name_ar=ar, emoji=emoji))
            # update in case changed
            c.name_bn=bn; c.name_en=en; c.name_ar=ar; c.emoji=emoji; c.is_active=True
            c.save()
            cat_map[code]=c
        # map bn category name to code
        name_to_code = {"স্টেশনারি":"stationery","কসমেটিকস":"cosmetics","খেলনা":"toys","অফিস":"office","আর্ট":"art","স্কুল":"school"}
        for sku, cat_bn, bn, en, ar, price, stock, emoji in PRODUCTS:
            cat = cat_map[name_to_code[cat_bn]]
            p, created = Product.objects.get_or_create(sku=sku, defaults=dict(
                category=cat, name_bn=bn, name_en=en, name_ar=ar,
                price=Decimal(str(price)), stock=stock, emoji=emoji, is_bestseller=(sku in ("rivin-0001","rivin-0008","rivin-0015","rivin-0019"))
            ))
            if not created:
                p.category=cat; p.name_bn=bn; p.name_en=en; p.name_ar=ar; p.price=Decimal(str(price)); p.stock=stock; p.emoji=emoji
                p.save()
        s = SiteSetting.get_solo()
        s.delivery_charge=Decimal('60.00'); s.min_order=Decimal('300.00'); s.save()
        dz, _ = DeliveryZone.objects.get_or_create(name="Dhaka", defaults=dict(charge=Decimal('60.00'), min_order=Decimal('300.00')))
        Coupon.objects.get_or_create(code="WELCOME10", defaults=dict(type="percent", value=Decimal('10.00'), is_active=True))
        self.stdout.write(self.style.SUCCESS(f"Seeded {Category.objects.count()} cats, {Product.objects.count()} products, bestsellers={SiteSetting.get_solo().bestsellers.count()}"))
