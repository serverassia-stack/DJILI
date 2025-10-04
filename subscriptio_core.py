# -*- coding: utf-8 -*-


"""
النواة الأساسية لمدير الاشتراكات
تحتوي على جميع الفئات والوظائف الأساسية
"""


import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import os
import json
import csv
import webbrowser
import smtplib
import shutil
import sqlite3
import threading
import requests
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from packaging import version


# ======================================================================
# 1. فئات النموذج الأساسية
# ======================================================================


class Subscription:
    """فئة تمثل اشتراكاً فردياً."""
    
    def __init__(self, name: str, date_str: str, price: float = 0.0, 
                 category: str = "عام", notes: str = "", subscription_id: Optional[int] = None):
        self.id = subscription_id or int(datetime.now().timestamp() * 1000)
        self.name = name
        self.date_str = date_str
        self.price = price
        self.category = category
        self.notes = notes
        self.created_at = datetime.now().isoformat()


    @property
    def date(self) -> datetime:
        return datetime.strptime(self.date_str, "%Y-%m-%d")


    @property
    def days_remaining(self) -> int:
        """عدد الأيام المتبقية حتى انتهاء الاشتراك."""
        today = datetime.now().date()
        subscription_date = self.date.date()
        return (subscription_date - today).days


    @property
    def status(self) -> str:
        """حالة الاشتراك بناءً على الأيام المتبقية."""
        days = self.days_remaining
        if days < 0:
            return "منتهي"
        elif days == 0:
            return "ينتهي اليوم"
        elif days <= 3:
            return "عاجل"
        elif days <= 7:
            return "قريب الانتهاء"
        else:
            return "نشط"


    @property
    def status_color(self) -> str:
        """لون الحالة."""
        colors = {
            'منتهي': '#ff4444',
            'ينتهي اليوم': '#ff8800',
            'عاجل': '#ff4444',
            'قريب الانتهاء': '#ffaa00',
            'نشط': '#44ff44'
        }
        return colors.get(self.status, '#44ff44')


    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date_str,
            'price': self.price,
            'category': self.category,
            'notes': self.notes,
            'created_at': self.created_at
        }


    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            name=data['name'],
            date_str=data['date'],
            price=data.get('price', 0.0),
            category=data.get('category', 'عام'),
            notes=data.get('notes', ''),
            subscription_id=data.get('id')
        )




class DateValidator:
    """فئة مساعدة للتحقق من صحة تنسيق التاريخ."""
    
    @staticmethod
    def is_valid(date_str: str, format: str = "%Y-%m-%d") -> bool:
        if not date_str:
            return False
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False


    @staticmethod
    def is_future_date(date_str: str) -> bool:
        """تتحقق مما إذا كان التاريخ في المستقبل."""
        try:
            input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            return input_date >= datetime.now().date()
        except ValueError:
            return False




class SubscriptionManager:
    """إدارة عمليات الحفظ والقراءة والتحديث والحذف."""
    
    def __init__(self, filename: str = "subscriptions.json"):
        self.filename = filename
        self._ensure_file_exists()


    def _ensure_file_exists(self):
        """يتأكد من وجود الملف وإنشاؤه إذا لم يكن موجوداً."""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([], f)


    def save_subscription(self, subscription: Subscription) -> bool:
        """يحفظ الاشتراك بعد التحقق من صحته."""
        try:
            # التحقق من صحة الإدخال
            if not subscription.name or len(subscription.name.strip()) < 2:
                raise ValueError("يجب أن يحتوي اسم الاشتراك على حرفين على الأقل.")
                
            if not DateValidator.is_valid(subscription.date_str):
                raise ValueError("تنسيق التاريخ غير صحيح. يجب أن يكون YYYY-MM-DD.")


            # تحميل الاشتراكات الحالية
            subscriptions = self._load_all()
            
            # إضافة الاشتراك الجديد
            subscriptions.append(subscription.to_dict())
            
            # حفظ الاشتراكات
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            raise Exception(f"خطأ في حفظ الاشتراك: {e}")


    def update_subscription(self, subscription_id: int, name: str, date_str: str, 
                          price: float, category: str, notes: str) -> bool:
        """تحديث اشتراك موجود."""
        try:
            subscriptions = self._load_all()
            
            for sub in subscriptions:
                if sub['id'] == subscription_id:
                    sub['name'] = name
                    sub['date'] = date_str
                    sub['price'] = price
                    sub['category'] = category
                    sub['notes'] = notes
                    break
            else:
                raise ValueError("الاشتراك غير موجود")
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            raise Exception(f"خطأ في تحديث الاشتراك: {e}")


    def delete_subscription(self, subscription_id: int) -> bool:
        """حذف اشتراك."""
        try:
            subscriptions = self._load_all()
            subscriptions = [sub for sub in subscriptions if sub['id'] != subscription_id]
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            raise Exception(f"خطأ في حذف الاشتراك: {e}")


    def load_subscriptions(self) -> List[Subscription]:
        """تحميل جميع الاشتراكات."""
        try:
            subscriptions_data = self._load_all()
            subscriptions = []
            
            for data in subscriptions_data:
                try:
                    subscription = Subscription.from_dict(data)
                    subscriptions.append(subscription)
                except Exception as e:
                    print(f"خطأ في تحميل اشتراك: {e}")
                    
            # ترتيب الاشتراكات حسب تاريخ الانتهاء
            subscriptions.sort(key=lambda x: x.date)
            return subscriptions
            
        except Exception as e:
            raise Exception(f"خطأ في تحميل الاشتراكات: {e}")


    def _load_all(self) -> List[Dict]:
        """تحميل البيانات الخام من الملف."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []


    def get_expiring_soon(self, days: int = 7) -> List[Subscription]:
        """الحصول على الاشتراكات التي تنتهي خلال عدد محدد من الأيام."""
        subscriptions = self.load_subscriptions()
        today = datetime.now().date()
        
        expiring = []
        for subscription in subscriptions:
            if 0 <= subscription.days_remaining <= days:
                expiring.append(subscription)
                
        return expiring


    def get_categories(self) -> List[str]:
        """الحصول على قائمة بالفئات الموجودة."""
        subscriptions = self.load_subscriptions()
        categories = set()
        for sub in subscriptions:
            categories.add(sub.category)
        return sorted(list(categories))


    def get_total_monthly_cost(self) -> float:
        """حساب التكلفة الشهرية الإجمالية."""
        subscriptions = self.load_subscriptions()
        return sum(sub.price for sub in subscriptions)


    def search_subscriptions(self, query: str, category: str = "الكل") -> List[Subscription]:
        """بحث في الاشتراكات."""
        subscriptions = self.load_subscriptions()
        
        if query:
            subscriptions = [s for s in subscriptions if query.lower() in s.name.lower()]
        
        if category != "الكل":
            subscriptions = [s for s in subscriptions if s.category == category]
            
        return subscriptions


    def create_backup(self, backup_path: str) -> bool:
        """إنشاء نسخة احتياطية من البيانات."""
        try:
            if os.path.exists(self.filename):
                backup_dir = Path(backup_path).parent
                backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.filename, backup_path)
                return True
            return False
        except Exception as e:
            raise Exception(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
    
    def restore_backup(self, backup_path: str) -> bool:
        """استعادة البيانات من نسخة احتياطية."""
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.filename)
                return True
            return False
        except Exception as e:
            raise Exception(f"خطأ في استعادة النسخة الاحتياطية: {e}")




class ExportManager:
    """مدير التصدير للصيغ المختلفة."""
    
    @staticmethod
    def to_csv(subscriptions: List[Subscription], filename: str):
        """تصدير إلى CSV."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['الاسم', 'التاريخ', 'السعر', 'الفئة', 'الحالة', 'الأيام المتبقية', 'ملاحظات'])
                
                for sub in subscriptions:
                    writer.writerow([
                        sub.name,
                        sub.date_str,
                        f"{sub.price:.2f}",
                        sub.category,
                        sub.status,
                        sub.days_remaining,
                        sub.notes
                    ])
            return True
        except Exception as e:
            raise Exception(f"خطأ في التصدير: {e}")


    @staticmethod
    def to_json(subscriptions: List[Subscription], filename: str):
        """تصدير إلى JSON."""
        try:
            data = [sub.to_dict() for sub in subscriptions]
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            raise Exception(f"خطأ في التصدير: {e}")




class SmartAlertSystem:
    """نظام تنبيهات ذكي."""
    
    def __init__(self, manager: SubscriptionManager):
        self.manager = manager
    
    def check_alerts(self) -> List[Dict]:
        """التحقق من جميع التنبيهات."""
        alerts = []
        subscriptions = self.manager.load_subscriptions()
        
        for subscription in subscriptions:
            # تنبيهات انتهاء الاشتراك
            if subscription.days_remaining <= 0:
                alerts.append({
                    'type': 'expired',
                    'title': 'اشتراك منتهي',
                    'message': f'الاشتراك "{subscription.name}" قد انتهى',
                    'subscription': subscription,
                    'priority': 'high'
                })
            elif subscription.days_remaining <= 3:
                alerts.append({
                    'type': 'urgent',
                    'title': 'اشتراك ينتهي قريباً',
                    'message': f'الاشتراك "{subscription.name}" ينتهي خلال {subscription.days_remaining} أيام',
                    'subscription': subscription,
                    'priority': 'medium'
                })
            elif subscription.days_remaining <= 7:
                alerts.append({
                    'type': 'warning',
                    'title': 'تنبيه بالانتهاء',
                    'message': f'الاشتراك "{subscription.name}" ينتهي خلال {subscription.days_remaining} أيام',
                    'subscription': subscription,
                    'priority': 'low'
                })
        
        return alerts
    
    def get_daily_summary(self) -> Dict:
        """الحصول على ملخص يومي."""
        alerts = self.check_alerts()
        return {
            'total_alerts': len(alerts),
            'high_priority': len([a for a in alerts if a['priority'] == 'high']),
            'medium_priority': len([a for a in alerts if a['priority'] == 'medium']),
            'alerts': alerts
        }




class AppSettings:
    """فئة لإدارة إعدادات التطبيق."""
    
    def __init__(self, settings_file: str = "app_settings.json"):
        self.settings_file = settings_file
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict:
        """تحميل الإعدادات."""
        default_settings = {
            'window_size': '1000x700',
            'theme': 'default',
            'language': 'ar',
            'auto_backup': True,
            'backup_interval_days': 7,
            'check_updates_on_start': True,
            'last_backup_date': None,
            'email_settings': {
                'smtp_server': 'smtp.gmail.com',
                'port': 587,
                'email': '',
                'password': '',
                'to_email': ''
            }
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # دمج الإعدادات المحملة مع الافتراضية
                    return {**default_settings, **loaded_settings}
            return default_settings
        except Exception:
            return default_settings
    
    def save_settings(self):
        """حفظ الإعدادات."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get(self, key: str, default=None):
        """الحصول على قيمة إعداد."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """تعيين قيمة إعداد."""
        self.settings[key] = value
        self.save_settings()




# ======================================================================
# 2. فئات الواجهة الرسومية
# ======================================================================


class SubscriptionFormDialog:
    """نافذة对话框 لإضافة أو تعديل اشتراك."""
    
    def __init__(self, parent, title, manager, subscription=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        self.manager = manager
        self.subscription = subscription
        self.result = None
        
        self._create_widgets()
        self._fill_data()
        
    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # حقل الاسم
        ttk.Label(main_frame, text="اسم الاشتراك:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.name_entry = ttk.Entry(main_frame, width=30, font=('Arial', 10))
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        # حقل التاريخ
        ttk.Label(main_frame, text="تاريخ التجديد (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.date_entry = ttk.Entry(main_frame, width=30, font=('Arial', 10))
        self.date_entry.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        # حقل السعر
        ttk.Label(main_frame, text="السعر الشهري:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.price_entry = ttk.Entry(main_frame, width=30, font=('Arial', 10))
        self.price_entry.grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        # حقل الفئة
        ttk.Label(main_frame, text="الفئة:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.category_combo = ttk.Combobox(main_frame, width=28, font=('Arial', 10))
        self.category_combo['values'] = ['عام', 'ترفيه', 'تعليم', 'أعمال', 'تسوق', 'أخرى']
        self.category_combo.grid(row=3, column=1, padx=10, pady=10, sticky='ew')
        
        # حقل الملاحظات
        ttk.Label(main_frame, text="ملاحظات:").grid(row=4, column=0, padx=10, pady=10, sticky='nw')
        self.notes_text = tk.Text(main_frame, width=30, height=4, font=('Arial', 10))
        self.notes_text.grid(row=4, column=1, padx=10, pady=10, sticky='ew')
        
        # أزرار التحكم
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        self.save_btn = ttk.Button(button_frame, text="💾 حفظ", command=self._save)
        self.save_btn.pack(side="left", padx=10)
        
        ttk.Button(button_frame, text="إلغاء", command=self.dialog.destroy).pack(side="left", padx=10)
        
        main_frame.columnconfigure(1, weight=1)
        
    def _fill_data(self):
        if self.subscription:
            self.name_entry.insert(0, self.subscription.name)
            self.date_entry.insert(0, self.subscription.date_str)
            self.price_entry.insert(0, str(self.subscription.price))
            self.category_combo.set(self.subscription.category)
            self.notes_text.insert('1.0', self.subscription.notes)
        else:
            self.category_combo.set('عام')
            self.price_entry.insert(0, "0.0")
            
    def _save(self):
        name = self.name_entry.get().strip()
        date_str = self.date_entry.get().strip()
        
        try:
            price = float(self.price_entry.get().strip() or "0")
        except ValueError:
            price = 0.0
            
        category = self.category_combo.get().strip() or "عام"
        notes = self.notes_text.get('1.0', 'end-1c').strip()
        
        try:
            if not name or len(name) < 2:
                raise ValueError("يجب أن يحتوي اسم الاشتراك على حرفين على الأقل.")
                
            if not DateValidator.is_valid(date_str):
                raise ValueError("تنسيق التاريخ غير صحيح. يجب أن يكون YYYY-MM-DD.")
                
            self.result = (name, date_str, price, category, notes)
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("خطأ في الإدخال", str(e))
            
    def show(self):
        self.dialog.wait_window()
        return self.result




class StatisticsDialog:
    """نافذة عرض الإحصائيات."""
    
    def __init__(self, parent, manager):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("الإحصائيات والتقارير")
        self.dialog.geometry("600x500")
        self.dialog.grab_set()
        
        self.manager = manager
        
        self._create_widgets()
        self._load_statistics()
        
    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="📊 الإحصائيات والتقارير", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # إنشاء Notebook لعرض التقارير المختلفة
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=10)
        
        # تبويب الإحصائيات العامة
        stats_frame = ttk.Frame(notebook, padding=10)
        notebook.add(stats_frame, text="الإحصائيات العامة")
        
        self.stats_text = tk.Text(stats_frame, height=15, width=60, font=('Arial', 10))
        self.stats_text.pack(fill="both", expand=True)
        
        # تبويب التكاليف
        costs_frame = ttk.Frame(notebook, padding=10)
        notebook.add(costs_frame, text="التكاليف")
        
        self.costs_text = tk.Text(costs_frame, height=15, width=60, font=('Arial', 10))
        self.costs_text.pack(fill="both", expand=True)
        
        ttk.Button(main_frame, text="إغلاق", command=self.dialog.destroy).pack(pady=10)
        
    def _load_statistics(self):
        subscriptions = self.manager.load_subscriptions()
        
        # الإحصائيات العامة
        total = len(subscriptions)
        active = len([s for s in subscriptions if s.status == 'نشط'])
        expiring_soon = len([s for s in subscriptions if s.status in ['ينتهي اليوم', 'عاجل', 'قريب الانتهاء']])
        expired = len([s for s in subscriptions if s.status == 'منتهي'])
        
        stats_content = f"""
الإحصائيات العامة:
----------------
• إجمالي الاشتراكات: {total}
• الاشتراكات النشطة: {active}
• الاشتراكات المنتهية: {expired}
• الاشتراكات قريبة الانتهاء: {expiring_soon}


التوزيع حسب الفئات:
------------------
"""
        categories = self.manager.get_categories()
        for category in categories:
            count = len([s for s in subscriptions if s.category == category])
            stats_content += f"• {category}: {count}\n"
        
        self.stats_text.insert('1.0', stats_content)
        
        # التكاليف
        total_cost = self.manager.get_total_monthly_cost()
        yearly_cost = total_cost * 12
        
        costs_content = f"""
التكاليف الشهرية:
----------------
• إجمالي التكلفة الشهرية: {total_cost:.2f} $
• التكلفة السنوية المتوقعة: {yearly_cost:.2f} $


التكاليف حسب الفئات:
-------------------
"""
        for category in categories:
            category_cost = sum(s.price for s in subscriptions if s.category == category)
            if category_cost > 0:
                percentage = (category_cost / total_cost) * 100 if total_cost > 0 else 0
                costs_content += f"• {category}: {category_cost:.2f} $ ({percentage:.1f}%)\n"
        
        self.costs_text.insert('1.0', costs_content)




class EnhancedSubscriptionApp:
    """التطبيق المحسن مع جميع الميزات."""
    
    def __init__(self, master):
        self.master = master
        self.settings = AppSettings()
        self.manager = SubscriptionManager()
        self.alert_system = SmartAlertSystem(self.manager)
        self.current_subscriptions = []
        
        self._setup_window()
        self._create_widgets()
        self._apply_settings()
        self._refresh_list()
        self._start_background_tasks()
    
    def _setup_window(self):
        """إعداد النافذة الرئيسية."""
        self.master.title("📅 مدير الاشتراكات المتقدم - النسخة الكاملة")
        self.master.geometry(self.settings.get('window_size', '1000x700'))
        
        # إعداد النمط
        self.style = ttk.Style()
        self.style.configure('Treeview', rowheight=28, font=('Arial', 10))
        self.style.configure('Treeview.Heading', font=('Arial', 11, 'bold'))
    
    def _create_widgets(self):
        """بناء واجهة المستخدم."""
        # إنشاء القوائم
        self._create_menu()
        
        main_frame = ttk.Frame(self.master, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # شريط العنوان
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(title_frame, text="📅 مدير الاشتراكات المتقدم - النسخة الكاملة", 
                 font=('Arial', 16, 'bold')).pack(side="left")
        
        # لوحة التحكم السريعة
        self._create_control_panel(main_frame)
        
        # شريط البحث والتصفية
        self._create_search_filter(main_frame)
        
        # جدول عرض الاشتراكات
        self._create_subscriptions_table(main_frame)
        
        # شريط الإحصائيات
        self._create_stats_bar(main_frame)
    
    def _create_control_panel(self, parent):
        """إنشاء لوحة التحكم السريعة."""
        control_frame = ttk.LabelFrame(parent, text="لوحة التحكم السريعة", padding=10)
        control_frame.pack(fill="x", pady=10)
        
        # صف الأزرار الأول
        row1_frame = ttk.Frame(control_frame)
        row1_frame.pack(fill="x", pady=5)
        
        ttk.Button(row1_frame, text="➕ إضافة اشتراك", 
                  command=self._add_subscription, width=15).pack(side="left", padx=5)
        ttk.Button(row1_frame, text="✏️ تعديل", 
                  command=self._edit_subscription, width=15).pack(side="left", padx=5)
        ttk.Button(row1_frame, text="🗑️ حذف", 
                  command=self._delete_subscription, width=15).pack(side="left", padx=5)
        ttk.Button(row1_frame, text="🔄 تحديث", 
                  command=self._refresh_list, width=15).pack(side="left", padx=5)
        
        # صف الأزرار الثاني
        row2_frame = ttk.Frame(control_frame)
        row2_frame.pack(fill="x", pady=5)
        
        ttk.Button(row2_frame, text="📊 إحصائيات", 
                  command=self._show_statistics, width=15).pack(side="left", padx=5)
        ttk.Button(row2_frame, text="📤 تصدير", 
                  command=self._export_data, width=15).pack(side="left", padx=5)
        ttk.Button(row2_frame, text="💾 نسخ احتياطي", 
                  command=self._backup_data, width=15).pack(side="left", padx=5)
        ttk.Button(row2_frame, text="⚙️ إعدادات", 
                  command=self._show_settings, width=15).pack(side="left", padx=5)
    
    def _create_search_filter(self, parent):
        """إنشاء شريط البحث والتصفية."""
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill="x", pady=10)
        
        ttk.Label(filter_frame, text="بحث:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind('<KeyRelease>', self._on_search)
        
        ttk.Label(filter_frame, text="الفئة:").pack(side="left", padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, width=15)
        self.category_combo['values'] = ['الكل'] + self.manager.get_categories()
        self.category_combo.set('الكل')
        self.category_combo.pack(side="left", padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', self._on_search)
    
    def _create_subscriptions_table(self, parent):
        """إنشاء جدول عرض الاشتراكات."""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)
        
        # إنشاء Treeview مع أعمدة
        columns = ('name', 'date', 'price', 'category', 'days_remaining', 'status', 'notes')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # تعريف العناوين
        self.tree.heading('name', text='اسم الاشتراك')
        self.tree.heading('date', text='تاريخ التجديد')
        self.tree.heading('price', text='السعر')
        self.tree.heading('category', text='الفئة')
        self.tree.heading('days_remaining', text='الأيام المتبقية')
        self.tree.heading('status', text='الحالة')
        self.tree.heading('notes', text='ملاحظات')
        
        # تعريف العرض
        self.tree.column('name', width=200)
        self.tree.column('date', width=120)
        self.tree.column('price', width=80)
        self.tree.column('category', width=100)
        self.tree.column('days_remaining', width=100)
        self.tree.column('status', width=100)
        self.tree.column('notes', width=200)
        
        # شريط التمرير
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ربط حدث النقر المزدوج
        self.tree.bind('<Double-1>', self._on_double_click)
    
    def _create_stats_bar(self, parent):
        """إنشاء شريط الإحصائيات."""
        self.stats_label = ttk.Label(parent, text="", font=('Arial', 10))
        self.stats_label.pack(pady=10)
    
    def _create_menu(self):
        """إنشاء قوائم التطبيق."""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # قائمة الملف
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="الملف", menu=file_menu)
        file_menu.add_command(label="تصدير البيانات", command=self._export_data)
        file_menu.add_command(label="نسخ احتياطي", command=self._backup_data)
        file_menu.add_separator()
        file_menu.add_command(label="خروج", command=self.master.quit)
        
        # قائمة الأدوات
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="الأدوات", menu=tools_menu)
        tools_menu.add_command(label="الإحصائيات", command=self._show_statistics)
        tools_menu.add_command(label="التنبيهات", command=self._show_alerts)
        
        # قائمة المساعدة
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="المساعدة", menu=help_menu)
        help_menu.add_command(label="عن البرنامج", command=self._about)
        help_menu.add_command(label="دليل الاستخدام", command=self._show_help)
    
    def _apply_settings(self):
        """تطبيق الإعدادات المحفوظة."""
        try:
            window_size = self.settings.get('window_size')
            if window_size:
                self.master.geometry(window_size)
        except Exception as e:
            print(f"خطأ في تطبيق الإعدادات: {e}")
    
    def _start_background_tasks(self):
        """بدء المهام الخلفية."""
        # التحقق من التنبيهات
        self._check_alerts_on_start()
        
        # بدء مراقبة التحديثات
        threading.Thread(target=self._check_auto_backup, daemon=True).start()
    
    def _check_alerts_on_start(self):
        """التحقق من التنبيهات عند البدء."""
        try:
            alerts = self.alert_system.get_daily_summary()
            if alerts['total_alerts'] > 0:
                high_priority = alerts['high_priority']
                if high_priority > 0:
                    messagebox.showwarning(
                        "تنبيهات عاجلة",
                        f"يوجد {high_priority} اشتراك منتهٍ يحتاج إلى اهتمام فوري!"
                    )
        except Exception as e:
            print(f"خطأ في التحقق من التنبيهات: {e}")
    
    def _check_auto_backup(self):
        """التحقق من النسخ الاحتياطي التلقائي."""
        try:
            if self.settings.get('auto_backup', True):
                last_backup = self.settings.get('last_backup_date')
                backup_interval = self.settings.get('backup_interval_days', 7)
                
                if not last_backup or (
                    datetime.now() - datetime.fromisoformat(last_backup) > 
                    timedelta(days=backup_interval)
                ):
                    self._create_auto_backup()
        except Exception as e:
            print(f"خطأ في النسخ الاحتياطي التلقائي: {e}")
    
    def _create_auto_backup(self):
        """إنشاء نسخة احتياطية تلقائية."""
        try:
            backup_dir = Path.home() / "SubscriptionManager" / "Backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.manager.create_backup(str(backup_file))
            self.settings.set('last_backup_date', datetime.now().isoformat())
            
        except Exception as e:
            print(f"خطأ في النسخ الاحتياطي التلقائي: {e}")


    # باقي الدوال (نفس الدوال السابقة مع تعديلات طفيفة)
    def _refresh_list(self, subscriptions=None):
        """تحديث قائمة الاشتراكات."""
        if subscriptions is None:
            try:
                subscriptions = self.manager.load_subscriptions()
                self.current_subscriptions = subscriptions
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر تحميل الاشتراكات: {e}")
                return
        
        # تحديث قائمة الفئات
        current_categories = ['الكل'] + self.manager.get_categories()
        self.category_combo['values'] = current_categories
        
        # مسح البيانات الحالية
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # إضافة البيانات الجديدة
        for subscription in subscriptions:
            status_color = self._get_status_color(subscription.status)
            self.tree.insert('', 'end', values=(
                subscription.name,
                subscription.date_str,
                f"{subscription.price:.2f} $",
                subscription.category,
                subscription.days_remaining,
                subscription.status,
                subscription.notes
            ), tags=(status_color,))
        
        # إعداد الألوان
        self.tree.tag_configure('expired', background='#ffcccc')
        self.tree.tag_configure('today', background='#ffddcc')
        self.tree.tag_configure('urgent', background='#ffcccc')
        self.tree.tag_configure('expiring_soon', background='#fff0cc')
        self.tree.tag_configure('active', background='#ccffcc')
        
        # تحديث الإحصائيات
        self._update_stats(subscriptions)
    
    def _get_status_color(self, status):
        """الحصول على لون الحالة."""
        colors = {
            'منتهي': 'expired',
            'ينتهي اليوم': 'today',
            'عاجل': 'urgent',
            'قريب الانتهاء': 'expiring_soon',
            'نشط': 'active'
        }
        return colors.get(status, 'active')
    
    def _update_stats(self, subscriptions):
        """تحديث الإحصائيات."""
        total = len(subscriptions)
        active = len([s for s in subscriptions if s.status == 'نشط'])
        expiring_soon = len([s for s in subscriptions if s.status in ['ينتهي اليوم', 'عاجل', 'قريب الانتهاء']])
        expired = len([s for s in subscriptions if s.status == 'منتهي'])
        total_cost = sum(s.price for s in subscriptions)
        
        stats_text = f"الإجمالي: {total} | نشط: {active} | قريب الانتهاء: {expiring_soon} | منتهي: {expired} | التكلفة الشهرية: {total_cost:.2f} $"
        self.stats_label.config(text=stats_text)
    
    def _on_search(self, event=None):
        """بحث في الاشتراكات."""
        search_term = self.search_var.get().lower()
        category = self.category_var.get()
        
        try:
            filtered = self.manager.search_subscriptions(search_term, category)
            self._refresh_list(filtered)
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر البحث: {e}")
    
    def _on_double_click(self, event):
        """التعامل مع النقر المزدوج."""
        self._edit_subscription()
    
    def _add_subscription(self):
        """إضافة اشتراك جديد."""
        dialog = SubscriptionFormDialog(self.master, "إضافة اشتراك جديد", self.manager)
        result = dialog.show()
        
        if result:
            name, date_str, price, category, notes = result
            subscription = Subscription(name, date_str, price, category, notes)
            
            try:
                self.manager.save_subscription(subscription)
                messagebox.showinfo("نجاح", f"تم حفظ الاشتراك '{name}' بنجاح.")
                self._refresh_list()
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر حفظ الاشتراك: {e}")
    
    def _edit_subscription(self):
        """تعديل اشتراك محدد."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "يرجى اختيار اشتراك للتعديل.")
            return
            
        try:
            selected_item = selected[0]
            item_index = self.tree.index(selected_item)
            
            if item_index < len(self.current_subscriptions):
                subscription = self.current_subscriptions[item_index]
                
                dialog = SubscriptionFormDialog(self.master, "تعديل اشتراك", self.manager, subscription)
                result = dialog.show()
                
                if result:
                    name, date_str, price, category, notes = result
                    self.manager.update_subscription(
                        subscription.id, name, date_str, price, category, notes
                    )
                    messagebox.showinfo("نجاح", "تم تحديث الاشتراك بنجاح.")
                    self._refresh_list()
                    
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر تعديل الاشتراك: {e}")
    
    def _delete_subscription(self):
        """حذف اشتراك محدد."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "يرجى اختيار اشتراك للحذف.")
            return
            
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الاشتراك؟"):
            try:
                selected_item = selected[0]
                item_index = self.tree.index(selected_item)
                
                if item_index < len(self.current_subscriptions):
                    subscription = self.current_subscriptions[item_index]
                    self.manager.delete_subscription(subscription.id)
                    messagebox.showinfo("نجاح", "تم حذف الاشتراك بنجاح.")
                    self._refresh_list()
                    
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر حذف الاشتراك: {e}")
    
    def _show_statistics(self):
        """عرض الإحصائيات."""
        StatisticsDialog(self.master, self.manager)
    
    def _export_data(self):
        """تصدير البيانات."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("ملف CSV", "*.csv"),
                    ("ملف JSON", "*.json"),
                    ("جميع الملفات", "*.*")
                ],
                title="تصدير البيانات"
            )
            
            if filename:
                subscriptions = self.manager.load_subscriptions()
                
                if filename.endswith('.csv'):
                    ExportManager.to_csv(subscriptions, filename)
                elif filename.endswith('.json'):
                    ExportManager.to_json(subscriptions, filename)
                
                messagebox.showinfo("نجاح", f"تم تصدير البيانات إلى: {filename}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر تصدير البيانات: {e}")
    
    def _backup_data(self):
        """إنشاء نسخة احتياطية."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("ملف النسخ الاحتياطي", "*.json")],
                title="إنشاء نسخة احتياطية"
            )
            
            if filename:
                if self.manager.create_backup(filename):
                    messagebox.showinfo("نجاح", f"تم إنشاء النسخة الاحتياطية: {filename}")
                else:
                    messagebox.showerror("خطأ", "تعذر إنشاء النسخة الاحتياطية")
                    
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر إنشاء النسخة الاحتياطية: {e}")
    
    def _show_settings(self):
        """عرض إعدادات التطبيق."""
        messagebox.showinfo("الإعدادات", "سيتم إضافة نافذة الإعدادات في الإصدار القادم")
    
    def _show_alerts(self):
        """عرض التنبيهات."""
        try:
            alerts = self.alert_system.get_daily_summary()
            if alerts['total_alerts'] == 0:
                messagebox.showinfo("التنبيهات", "لا توجد تنبيهات حالياً")
            else:
                alert_text = f"إجمالي التنبيهات: {alerts['total_alerts']}\n"
                alert_text += f"عاجل: {alerts['high_priority']}\n"
                alert_text += f"متوسط: {alerts['medium_priority']}\n\n"
                
                for alert in alerts['alerts'][:5]:  # عرض أول 5 تنبيهات فقط
                    alert_text += f"• {alert['message']}\n"
                
                messagebox.showwarning("التنبيهات", alert_text)
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر تحميل التنبيهات: {e}")
    
    def _about(self):
        """عرض معلومات عن البرنامج."""
        about_text = """
مدير الاشتراكات المتقدم - الإصدار الكامل


📅 نظام متكامل لإدارة الاشتراكات والمدفوعات الدورية


المميزات:
• إدارة كاملة للاشتراكات
• تنبيهات بالاشتراكات المنتهية
• إحصائيات وتقارير متقدمة
• تصدير البيانات بمختلف الصيغ
• واجهة مستخدم عربية بدعم كامل


الإصدار: 2.0.0
        """
        messagebox.showinfo("عن البرنامج", about_text)
    
    def _show_help(self):
        """عرض دليل الاستخدام."""
        help_text = """
دليل استخدام البرنامج:


1. إضافة اشتراك جديد:
   - انقر على "إضافة اشتراك"
   - املأ البيانات المطلوبة
   - احفظ البيانات


2. تعديل أو حذف اشتراك:
   - اختر الاشتراك من القائمة
   - انقر على "تعديل" أو "حذف"


3. البحث والتصفية:
   - استخدم حقل البحث للبحث بالاسم
   - استخدم قائمة الفئات للتصفية


4. التصدير والنسخ الاحتياطي:
   - استخدم أزرار "تصدير" و"نسخ احتياطي"
   - اختر الصيغة المطلوبة


5. الإحصائيات:
   - انقر على "إحصائيات" لعرض التقارير
        """
        messagebox.showinfo("دليل الاستخدام", help_text)
