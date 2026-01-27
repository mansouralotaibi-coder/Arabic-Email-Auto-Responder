#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_cell_magic('writefile', 'config.py', '\nimport os\nimport re\nimport io\nimport email\nimport time\nimport json\nimport torch\nimport shutil\nimport imaplib\nimport smtplib\nimport tempfile\nimport pandas as pd\nimport fitz  \nfrom PIL import Image\nfrom bs4 import BeautifulSoup\nfrom datetime import datetime, timedelta\nfrom email.header import decode_header\nfrom email.mime.text import MIMEText\nfrom hijri_converter import Hijri\nfrom langchain.docstore.document import Document\nfrom langchain.embeddings import HuggingFaceEmbeddings\nfrom langchain.vectorstores import FAISS\nfrom langchain.text_splitter import RecursiveCharacterTextSplitter\nfrom langchain.retrievers import BM25Retriever, ParentDocumentRetriever\nfrom langchain.storage import InMemoryStore\nfrom transformers import AutoTokenizer, AutoModelForCausalLM, pipeline\nfrom googleapiclient.discovery import build\nfrom google.oauth2 import service_account\nfrom ArabicOcr import arabicocr  \nimport gc  \nimport openpyxl  \nimport json\nimport re\nfrom datetime import datetime, timedelta\nfrom hijri_converter import Hijri, Gregorian\nfrom googleapiclient.discovery import build\nfrom google.oauth2 import service_account\nimport json\nimport re\nimport re\nimport json\n')


# In[2]:


get_ipython().run_cell_magic('writefile', '-a config.py', 'MODEL_ID = "Qwen/Qwen3-32B"\n#MODEL_ID = "Qwen/Qwen3-14B"\n#MODEL_ID = "Qwen/Qwen3-30B-A3B"\n#MODEL_ID = "Qwen/Qwen2.5-32B-Instruct" \nGMAIL_EMAIL = "eng.mansour.issa@gmail.com"\nAPP_PASSWORD = "sugtcfmplficwqzr"\nCALENDAR_ID = "eng.mansour.issa@gmail.com"\nSERVICE_ACCOUNT_FILE = \'kaust-481121-7ec069937b0c.json\'\nDEVICE = \'cuda\' if torch.cuda.is_available() else \'cpu\'\nSCOPES = [\'https://www.googleapis.com/auth/calendar\']\nIMAP_SERVER = "imap.gmail.com"\nSMTP_SERVER = "smtp.gmail.com"\ntokenizer = AutoTokenizer.from_pretrained(MODEL_ID)\nmodel = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype="auto", device_map="auto")\nmodel = torch.compile(model)\nllm_pipeline = pipeline(\n    "text-generation", \n    model=model, \n    tokenizer=tokenizer, \n    max_new_tokens=1024,\n    # الإضافات الجديدة:\n    do_sample=True  ,    \n    temperature=0.1,     \n    top_p=0.90,           \n    repetition_penalty=1.15 \n)\n')


# In[ ]:




