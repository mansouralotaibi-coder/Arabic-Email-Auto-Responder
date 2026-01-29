#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_cell_magic('writefile', 'RulesForIntents.py', '\nimport os\nimport re\nimport io\nimport email\nimport time\nimport json\nimport torch\nimport shutil\nimport imaplib\nimport smtplib\nimport tempfile\nimport pandas as pd\nimport fitz  \nfrom PIL import Image\nfrom bs4 import BeautifulSoup\nfrom datetime import datetime, timedelta\nfrom email.header import decode_header\nfrom email.mime.text import MIMEText\nfrom hijri_converter import Hijri\nfrom langchain.docstore.document import Document\nfrom langchain.embeddings import HuggingFaceEmbeddings\nfrom langchain.vectorstores import FAISS\nfrom langchain.text_splitter import RecursiveCharacterTextSplitter\nfrom langchain.retrievers import BM25Retriever, ParentDocumentRetriever\nfrom langchain.storage import InMemoryStore\nfrom transformers import AutoTokenizer, AutoModelForCausalLM, pipeline\nfrom googleapiclient.discovery import build\nfrom google.oauth2 import service_account\nfrom ArabicOcr import arabicocr  \nimport gc  \nimport openpyxl  \nimport json\nimport re\nfrom datetime import datetime, timedelta\nfrom hijri_converter import Hijri, Gregorian\nfrom googleapiclient.discovery import build\nfrom google.oauth2 import service_account\nimport json\nimport re\nimport re\nimport json\n\n\nfrom config import tokenizer, llm_pipeline, DEVICE, SERVICE_ACCOUNT_FILE, SCOPES\n')


# In[2]:


get_ipython().run_cell_magic('writefile', '-a RulesForIntents.py', '\nRULES_DIR = "intent_rules"\nos.makedirs(RULES_DIR, exist_ok=True)\n\ndef load_intent_rules(intent):\n    """\n    قراءة القواعد الخاصة بنية معينة من ملفها الخاص.\n    """\n    file_path = os.path.join(RULES_DIR, f"{intent}_rules.txt")\n    if os.path.exists(file_path):\n        try:\n            with open(file_path, \'r\', encoding=\'utf-8\') as f:\n                return f.read().strip()\n        except Exception as e:\n            print(f"⚠ خطأ في قراءة ملف القواعد لـ {intent}: {e}")\n            return ""\n    return ""\n')


# In[3]:


get_ipython().run_cell_magic('writefile', '-a RulesForIntents.py', '\ndef deduce_administrative_rule(incoming_body, sent_body, intent):\n    """\n    وظيفة المحلل: مقارنة الوارد بالصادر لاستنتاج القاعدة الإدارية.\n    """\n    system_prompt = """\nدورك: مستخرج حقائق صارم (Strict Fact Extractor).\nالمهمة: استخراج منطق الرد (Logic) وتحويله إلى JSON بناءً على النصوص أدناه فقط.\n\nالقواعد الصارمة:\n1. "ما ليس في النص، ليس موجوداً": يمنع منعاً باتاً إضافة شروط أو إجراءات تخمينية.\n2. جمّد المتغيرات: تجاهل التواريخ والأسماء، وركز على (المسميات الوظيفية) و(الإجراءات).\n3. المصدر الوحيد للحقيقة هو: (الرسالة الواردة) و (الرد النموذجي).\n\nالمخرجات JSON فقط:\n{\n  "condition": "سبب المراسلة (من النص الوارد)",\n  "action": "الإجراء المتخذ (من النص الصادر)",\n  "recipient": "المسمى الوظيفي للمستلم (حرفياً من الصادر)",\n  "key_phrases": ["العبارات الثابتة فقط"],\n  "formatting_note": "تنسيق خاص إن وجد"\n}\n"""\n    \n    user_prompt = f"""\n=== الرسالة الواردة (Incoming) ===\n{incoming_body}\n\n=== الرد النموذجي (Ground Truth) ===\n{sent_body}\n\n=== نية المراسلة ===\n{intent}\n\nاستخرج القاعدة التي تجعل الرد مطابقاً تماماً للرد النموذجي (خاصة المسميات والإجراءات المالية/الإدارية):\n"""\n\n    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]\n    \n    try:\n        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)\n        output = llm_pipeline(text_input, temperature=0.1, max_new_tokens=512)[0][\'generated_text\'].replace(text_input, "").strip()\n        return output\n    except Exception as e:\n        print(f"⚠ خطأ في استنتاج القاعدة: {e}")\n        return None\n')


# In[4]:


get_ipython().run_cell_magic('writefile', '-a RulesForIntents.py', '\ndef update_intent_rules_file(intent, new_rule):\n    """\n    دمج القاعدة الجديدة مع القواعد القديمة في ملف النية المحدد.\n    """\n    if not new_rule: return\n    \n    file_path = os.path.join(RULES_DIR, f"{intent}_rules.txt")\n    existing_rules = ""\n    \n    if os.path.exists(file_path):\n        with open(file_path, \'r\', encoding=\'utf-8\') as f:\n            existing_rules = f.read()\n            \n    # استخدام LLM لدمج القواعد وتنظيفها (De-duplication & Merging)\n    system_prompt =f"""\nدورك: دمج نصوص آلي (Robot Merger).\nالمهمة: دمج (القاعدة الجديدة) داخل (القائمة الحالية) وإزالة التكرار.\n\nالقيود الصارمة:\n1. لا تؤلف: يمنع إضافة أي قاعدة لم ترد في المدخلات.\n2. لا تستنتج: ادمج النصوص المتطابقة فقط.\n3. التحديث: إذا تعارضت قاعدة جديدة مع قديمة، اعتمد الجديدة.\n4. المخرج: قائمة نصية فقط، مختصرة وواضحة.\n\nالصيغة المطلوبة:\n- **[الحالة]**: التوجيه لـ [المسمى]، الإجراء: [الفعل].\n"""\n\n    user_prompt = f"""\n--- القواعد الحالية ---\n{existing_rules}\n\n--- القاعدة الجديدة ---\n{new_rule}\n\nأعد صياغة القائمة المحدثة (بالعربية المختصرة):\n"""\n\n    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]\n\n    try:\n        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)\n        updated_rules = llm_pipeline(text_input, temperature=0.1, max_new_tokens=1024)[0][\'generated_text\'].replace(text_input, "").strip()\n        \n        # حفظ القواعد المحدثة في الملف\n        with open(file_path, \'w\', encoding=\'utf-8\') as f:\n            f.write(updated_rules)\n        print(f"✅ تم تحديث ملف القواعد للنية: {intent}")\n        \n    except Exception as e:\n        print(f"⚠ خطأ في تحديث ملف القواعد: {e}")\n')


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




