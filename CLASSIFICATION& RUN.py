#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import re
import io
import email
import time
import json
import torch
import shutil
import imaplib
import smtplib
import tempfile
import pandas as pd
import fitz  
from PIL import Image
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.header import decode_header
from email.mime.text import MIMEText
from hijri_converter import Hijri
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import BM25Retriever, ParentDocumentRetriever
from langchain.storage import InMemoryStore
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from googleapiclient.discovery import build
from google.oauth2 import service_account
from ArabicOcr import arabicocr  
import gc  
import openpyxl  
import json
import re
from datetime import datetime, timedelta
from hijri_converter import Hijri, Gregorian
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
import re
import re
import json






# In[2]:


from config import MODEL_ID, DEVICE, GMAIL_EMAIL, APP_PASSWORD , CALENDAR_ID , SERVICE_ACCOUNT_FILE , DEVICE , SCOPES , IMAP_SERVER , SMTP_SERVER , tokenizer , model , llm_pipeline


# In[3]:


from processor import FileProcessor
from rag_engine import find_parent_large_chunks , initialize_fixed_knowledge , regex_split_documents , get_fixed_context , get_attachment_context
from services import safe_decode , html_to_text , send_reply , check_new_emails , update_email_history , create_draft , sync_sent_emails_to_history 
from All_intents import get_current_context , arabic_to_english_numbers , calculate_next_weekday , calculate_next_hijri , process_gregorian_date , process_hijri_date , extract_appointment_info , generate_llm_response , handle_calendar_intent , get_isolated_knowledge_context , handle_general_inquiries , handle_administrative_procedures , handle_administrative_procedures , handle_hr_procedures , rag_answer_email , handle_attachment_special_requests , handle_User_Requests 
from RulesForIntents import RULES_DIR , load_intent_rules , deduce_administrative_rule , update_intent_rules_file  






# In[4]:


def classify_email_intent(email_body, sender_info):
    """
    محلل النية المركزي: يقوم بتصنيف الإيميل إلى فئة محددة لتوجيهه للدالة المناسبة مباشرة.
    """
    system_prompt = """
    أنت نظام خبير في تصنيف المراسلات الإدارية. مهمتك هي قراءة الإيميل وتصنيفه بدقة إلى فئة واحدة فقط من الفئات التالية:
    1. "CALENDAR": إذا كان النص يتعلق بشكل صريح بطلب موعد جديد، تأكيد موعد، أو طلب حضور في وقت محدد .
    2. "HR": إذا كان النص يتعلق بطلبات الموظفين الشخصية (إجازة، دورة تدريبية، دراسة).
    4. "INQUIRY": إذا كان النص سؤالاً صريحاً عن معلومات نظامية أو بيانات موظفين أو إجراءات (وليس بلاغ صيانة).
    5. "RAG_MAINTENANCE": إذا كان النص بلاغ صيانة، شكوى فنية، طلب إصلاح، أو أي موضوع عام آخر يحتاج بحث في كافة المراجع ولايطلب تحديد موعد بشكل صريح
    6. "User_Requests": اذا كان يطلب بشكل صريح كتابة ايميل او يطلب بحث عن معلومات في المرفقات حتى لو تعارض مع الفئات اعلاه.
    أعد النتيجة بصيغة JSON فقط:
    {"intent": "الفئة_هنا"}
    """
    
    prompt = f"المرسل: {sender_info}\nنص الإيميل: {email_body}"
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]

    try:
        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True , enable_thinking=False)
        outputs = llm_pipeline(text_input, temperature=0.01) # حرارة منخفضة جداً للالتزام بالتصنيف
        raw_output = outputs[0]['generated_text'].replace(text_input, "").strip()
        
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group()).get("intent", "RAG_MAINTENANCE")
    except Exception as e:
        print(f"⚠ خطأ في تحليل النية المركزي: {e}")
    
    return "RAG_MAINTENANCE" 


# In[5]:


def log_draft_for_evaluation(msg_id, sender, intent, incoming_body, bot_draft):
    """
    حفظ بيانات المسودة في ملف إكسل لغرض التقييم لاحقاً.
    """
    file_path = "evaluation_data.xlsx"
    new_data = {
        "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Message-ID": [msg_id],
        "Sender": [sender],
        "Intent": [intent],
        "Incoming Body": [incoming_body],
        "Bot Draft": [bot_draft],
        "Ground Truth": [""]  # يترك فارغاً لتقوم أنت بتعبئته
    }
    
    df_new = pd.DataFrame(new_data)
    
    try:
        if os.path.exists(file_path):
            df_existing = pd.read_excel(file_path)
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            # منع التكرار بناءً على Message-ID
            df_final.drop_duplicates(subset=['Message-ID'], keep='first', inplace=True)
            df_final.to_excel(file_path, index=False)
        else:
            df_new.to_excel(file_path, index=False)
        print(f"📊 تم تسجيل المسودة في ملف التقييم (ID: {msg_id})")
    except Exception as e:
        print(f"⚠ خطأ في تحديث ملف الإكسل: {e}")
    


# In[ ]:


def run_auto_bot():
    print("🚀 جاري تشغيل بوت الرد الآلي المطور (نظام التقييم والتعلم الذاتي)...")
    
    # إعداد النماذج والمعالجات
    embed_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3", 
        model_kwargs={'device': DEVICE}
    )
    processor = FileProcessor()
    
    # البناء الأولي للقاعدة المعرفية الثابتة
    kb = initialize_fixed_knowledge(processor, embed_model)
    if not kb:
        print("❌ فشل بناء القاعدة المعرفية الثابتة.")
        return
    
    print("✅ تم تفعيل النظام بالكامل. البوت في وضع الاستعداد...")
    
    while True:
        try:
            # 1. فحص البريد الوارد ومعالجته
            new_emails = check_new_emails(processor)
            
            for sender, subject, body, attachments, msg_id in new_emails:
                print(f"\n📩 إيميل جديد من: {sender}")
                
                # تصنيف النية (Intent Classification)
                intent = classify_email_intent(body, sender)
                print(f"🎯 النية المكتشفة: {intent}")

                # تسجيل التاريخ المحلي في ملف النص
                update_email_history("إيميل وارد", body, msg_id=msg_id, intent=intent)
                
                reply_text = None

                # أ. معالجة المرفقات (إن وجدت)
                if attachments:
                    reply_text = handle_attachment_special_requests(attachments, body, processor, embed_model, sender)

                # ب. معالجة النصوص حسب النية إذا لم يتم الرد عبر المرفقات
                if not reply_text:
                    if intent == "CALENDAR":
                        reply_text = handle_calendar_intent(body, sender)
                    elif intent == "HR":
                        reply_text = handle_hr_procedures(body, sender)
                    elif intent == "ADMIN":
                        reply_text = handle_administrative_procedures(body, sender)
                    elif intent == "INQUIRY":
                        reply_text = handle_general_inquiries(body, sender, kb)
                    elif intent == "User_Requests":
                        reply_text = handle_User_Requests(body, sender, kb, attachments, processor, embed_model)

                    # ج. الرد الافتراضي باستخدام RAG في حال عدم انطباق الشروط أعلاه
                    if not reply_text:
                        fixed_ctx = get_fixed_context(body, kb)
                        reply_text = rag_answer_email(body, fixed_ctx)

                # د. إنشاء المسودة وتوثيقها للتقييم (الميزة الجديدة)
                if reply_text:
                    # إنشاء المسودة في Gmail
                    draft_success = create_draft(sender, subject, reply_text, reply_to_id=msg_id)
                    
                    if draft_success:
                        # توثيق الرد في ملف الإكسل للمقارنة بـ Ground Truth لاحقاً
                        log_draft_for_evaluation(msg_id, sender, intent, body, reply_text)
                
                # هـ. تنظيف الملفات المؤقتة
                if attachments:
                    for att in attachments:
                        if os.path.exists(att): os.remove(att)

            # 2. مزامنة الإيميلات المرسلة والتعلم من ردود المدير البشرية
            did_learn_something_new = sync_sent_emails_to_history()
            
            # تحديث القاعدة المعرفية إذا تم استنتاج قاعدة إدارية جديدة
            if did_learn_something_new:
                print("♻️ تم اكتشاف قواعد جديدة.. جاري تحديث الدماغ (Knowledge Base)...")
                kb = initialize_fixed_knowledge(processor, embed_model)
                print("✅ تم تحديث الدماغ بنجاح.")
            
        except Exception as e:
            print(f"⚠ خطأ غير متوقع في الحلقة الرئيسية: {e}")
            time.sleep(5)
        
        # الانتظار قبل الفحص التالي
        time.sleep(10)
if __name__ == "__main__":
    run_auto_bot()


# In[ ]:





# In[ ]:




