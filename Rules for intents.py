#!/usr/bin/env python
# coding: utf-8

# In[9]:


get_ipython().run_cell_magic('writefile', 'RulesForIntents.py', '\nimport os\nimport re\nimport io\nimport email\nimport time\nimport json\nimport torch\nimport shutil\nimport imaplib\nimport smtplib\nimport tempfile\nimport pandas as pd\nimport fitz  \nfrom PIL import Image\nfrom bs4 import BeautifulSoup\nfrom datetime import datetime, timedelta\nfrom email.header import decode_header\nfrom email.mime.text import MIMEText\nfrom hijri_converter import Hijri\nfrom langchain.docstore.document import Document\nfrom langchain.embeddings import HuggingFaceEmbeddings\nfrom langchain.vectorstores import FAISS\nfrom langchain.text_splitter import RecursiveCharacterTextSplitter\nfrom langchain.retrievers import BM25Retriever, ParentDocumentRetriever\nfrom langchain.storage import InMemoryStore\nfrom transformers import AutoTokenizer, AutoModelForCausalLM, pipeline\nfrom googleapiclient.discovery import build\nfrom google.oauth2 import service_account\nfrom ArabicOcr import arabicocr  \nimport gc  \nimport openpyxl  \nimport json\nimport re\nfrom datetime import datetime, timedelta\nfrom hijri_converter import Hijri, Gregorian\nfrom googleapiclient.discovery import build\nfrom google.oauth2 import service_account\nimport json\nimport re\nimport re\nimport json\n\n\nfrom config import tokenizer, llm_pipeline, DEVICE, SERVICE_ACCOUNT_FILE, SCOPES\n')


# In[10]:


get_ipython().run_cell_magic('writefile', '-a RulesForIntents.py', '\nRULES_DIR = "intent_rules"\nos.makedirs(RULES_DIR, exist_ok=True)\n\ndef load_intent_rules(intent):\n    """\n    قراءة القواعد الخاصة بنية معينة من ملفها الخاص.\n    """\n    file_path = os.path.join(RULES_DIR, f"{intent}_rules.txt")\n    if os.path.exists(file_path):\n        try:\n            with open(file_path, \'r\', encoding=\'utf-8\') as f:\n                return f.read().strip()\n        except Exception as e:\n            print(f"⚠ خطأ في قراءة ملف القواعد لـ {intent}: {e}")\n            return ""\n    return ""\n')


# In[11]:


get_ipython().run_cell_magic('writefile', '-a RulesForIntents.py', '\ndef deduce_administrative_rule(incoming_body, sent_body, intent):\n    """\n    وظيفة المحلل: مقارنة الوارد بالصادر لاستنتاج القاعدة الإدارية.\n    """\n    system_prompt = """\nأنت خبير تحليل نظم (System Analyst). مهمتك استخراج "الخوارزمية الإدارية" التي ربطت "الطلب" بـ "الرد".\n\nالتعليمات:\n1. حلل السبب الجذري: لماذا تم اتخاذ هذا الإجراء تحديداً؟ (هل تم الرفض بسبب نقص شرط؟ هل تم القبول بشرط معين؟).\n2. استخرج "المتغيرات": لمن تم التوجيه؟ ما هي نبرة الرد (حازمة/مرنة)؟\n3. المخرجات: صغ قاعدة واحدة صارمة بصيغة: "IF [الشرط] THEN [الإجراء] USING [النبرة/الصيغة]".\n\nمثال: "إذا طلب الموظف إجازة ولم يرفق البديل، ارفض الطلب فوراً بصيغة حازمة، ووجه الخطاب للموظف مباشرة".\n"""\n    \n    user_prompt = f"""\n--- الإيميل الوارد ---\n{incoming_body}\n\n--- الإيميل الصادر (الجواب النهائي) ---\n{sent_body}\n\n--- سياق النية ---\n{intent}\n\nاستخرج القاعدة الإدارية المستنتجة بوضوح واختصار:\n"""\n\n    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]\n    \n    try:\n        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)\n        output = llm_pipeline(text_input, temperature=0.1, max_new_tokens=512)[0][\'generated_text\'].replace(text_input, "").strip()\n        return output\n    except Exception as e:\n        print(f"⚠ خطأ في استنتاج القاعدة: {e}")\n        return None\n')


# In[12]:


get_ipython().run_cell_magic('writefile', '-a RulesForIntents.py', '\ndef update_intent_rules_file(intent, new_rule):\n    """\n    دمج القاعدة الجديدة مع القواعد القديمة في ملف النية المحدد.\n    """\n    if not new_rule: return\n    \n    file_path = os.path.join(RULES_DIR, f"{intent}_rules.txt")\n    existing_rules = ""\n    \n    if os.path.exists(file_path):\n        with open(file_path, \'r\', encoding=\'utf-8\') as f:\n            existing_rules = f.read()\n            \n    # استخدام LLM لدمج القواعد وتنظيفها (De-duplication & Merging)\n    system_prompt = f"""\nأنت مدير قاعدة المعرفة (Knowledge Base Manager) للقسم ({intent}).\nمهمتك: دمج "القاعدة الجديدة" مع "القائمة الحالية" لإنتاج قائمة محدثة ونظيفة.\n\nالبروتوكول:\n1. الأولوية للأحدث: إذا تعارضت قاعدة جديدة مع قديمة، احذف القديمة واعتمد الجديدة.\n2. الدمج الذكي: ادمج القواعد المتشابهة في نقطة واحدة شاملة.\n3. التنسيق: اجعل القواعد بصيغة أوامر تنفيذية مباشرة (Do X when Y). لا تستخدم السرد.\n\nالمخرجات: القائمة النهائية فقط.\n"""\n\n    user_prompt = f"""\n--- القواعد الحالية ---\n{existing_rules}\n\n--- القاعدة الجديدة ---\n{new_rule}\n\nالقائمة المحدثة للقواعد:\n"""\n\n    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]\n\n    try:\n        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)\n        updated_rules = llm_pipeline(text_input, temperature=0.1, max_new_tokens=1024)[0][\'generated_text\'].replace(text_input, "").strip()\n        \n        # حفظ القواعد المحدثة في الملف\n        with open(file_path, \'w\', encoding=\'utf-8\') as f:\n            f.write(updated_rules)\n        print(f"✅ تم تحديث ملف القواعد للنية: {intent}")\n        \n    except Exception as e:\n        print(f"⚠ خطأ في تحديث ملف القواعد: {e}")\n')


# In[ ]:





# In[ ]:





# In[ ]:




