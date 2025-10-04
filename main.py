#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
مدير الاشتراكات المتقدم - النسخة الكاملة
الإصدار: 2.0.0
"""


import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import threading
from typing import List, Dict, Optional


# إضافة المسار الحالي إلى مسار الاستيراد
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


try:
    from subscription_core import (
        Subscription, SubscriptionManager, DateValidator,
        ExportManager, SmartAlertSystem, AppSettings,
        EnhancedSubscriptionApp
    )
except ImportError as e:
    print(f"خطأ في استيراد المكتبات: {e}")
    print("يرجى التأكد من تثبيت جميع المتطلبات:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def setup_logging():
    """إعداد نظام التسجيل."""
    try:
        log_dir = Path.home() / "SubscriptionManager" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "app.log", encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info("بدأ تشغيل التطبيق")
    except Exception as e:
        print(f"خطأ في إعداد التسجيل: {e}")


def check_dependencies():
    """التحقق من التبعيات الأساسية."""
    try:
        import tkinter
        import json
        import datetime
        return True
    except ImportError as e:
        print(f"التبعيات الأساسية غير متوفرة: {e}")
        return False


def create_sample_data():
    """إنشاء بيانات نموذجية للمستخدم الجديد."""
    try:
        manager = SubscriptionManager()
        subscriptions = manager.load_subscriptions()
        
        if not subscriptions:
            # إضافة اشتراكات نموذجية
            sample_subs = [
                Subscription("نيتفليكس", "2024-02-15", 45.0, "ترفيه", "اشتراك شهري"),
                Subscription("يوتيوب بريميوم", "2024-03-01", 35.0, "ترفيه", "موسيقى وفيديوهات"),
                Subscription("أمازون برايم", "2024-01-30", 40.0, "تسوق", "شحن مجاني"),
                Subscription("Microsoft 365", "2024-04-10", 60.0, "أعمال", "حزمة أوفيس"),
                Subscription("Adobe Creative", "2024-05-05", 120.0, "تعليم", "تصميم وجرافيكس"),
            ]
            
            for sub in sample_subs:
                manager.save_subscription(sub)
                
            logging.info("تم إنشاء البيانات النموذجية")
    except Exception as e:
        logging.error(f"خطأ في إنشاء البيانات النموذجية: {e}")


def main():
    """الدالة الرئيسية لتشغيل التطبيق."""
    try:
        # إعداد التسجيل
        setup_logging()
        
        # التحقق من التبعيات
        if not check_dependencies():
            messagebox.showerror(
                "خطأ", 
                "المكتبات الأساسية غير مثبتة!\n"
                "يرجى التأكد من تثبيت Python بشكل صحيح."
            )
            return
        
        # إنشاء النافذة الرئيسية
        root = tk.Tk()
        
        # إعداد عنوان النافذة وأيقونتها
        root.title("📅 مدير الاشتراكات المتقدم - النسخة الكاملة")
        root.geometry("1200x800")
        
        # محاولة تحميل الأيقونة
        try:
            icon_path = os.path.join(current_dir, "app_icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"لم يتمكن من تحميل الأيقونة: {e}")
        
        # إنشاء بيانات نموذجية للمستخدمين الجدد
        create_sample_data()
        
        # بدء التطبيق الرئيسي
        app = EnhancedSubscriptionApp(root)
        
        # تشغيل التطبيق
        logging.info("بدء واجهة المستخدم")
        root.mainloop()
        
    except Exception as e:
        logging.error(f"خطأ غير متوقع: {e}")
        messagebox.showerror(
            "خطأ فادح", 
            f"حدث خطأ غير متوقع في التطبيق:\n{e}\n\n"
            "يرجى إعادة تشغيل التطبيق. إذا استمر الخطأ، "
            "اتصل بالدعم الفني."
        )


if __name__ == "__main__":
    # تغيير الترميز لدعم العربية في console (للاستخدام في Windows)
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # UTF-8
        except:
            pass
    
    print("=" * 60)
    print("🚀 بدء تشغيل مدير الاشتراكات المتقدم")
    print("=" * 60)
    print("الإصدار: 2.0.0")
    print("المطور: نظام إدارة الاشتراكات")
    print("=" * 60)
    
    main()
