# AI-Powered Arabic Email Automation & RAG System

This project is a sophisticated, AI-driven automation system designed to handle official Arabic email communications. It utilizes Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and Optical Character Recognition (OCR) to classify, process, and draft responses to various types of administrative, HR, and technical emails.

A key feature of this system is its **Self-Learning Capability**, which allows it to deduce and update administrative rules by analyzing manual replies sent by the human manager.

##  Project Structure

The project is modularized into specific components handling configuration, processing, logic, and execution.

| File Name | Description |
| :--- | :--- |
| **`CLASSIFICATION& RUN.py`** | **Entry Point.** The main execution script. It runs the continuous loop to check emails, uses an LLM to classify user intents (HR, Admin, Calendar, etc.), and routes the request to the appropriate handler. It also manages the evaluation logging. |
| **`config.py`** | **Configuration Hub.** Contains global constants, API keys (Gmail, Google Calendar), model parameters (Qwen-32B), and initializes the core LLM pipeline and tokenizer. |
| **`processor.py`** | **ETL & OCR Engine.** Handles file ingestion. It extracts text from PDF (using `ArabicOcr`), Excel, Word, and text files. It includes logic to reconstruct smart text from OCR bounding boxes. |
| **`rag_engine.py`** | **RAG Core.** Manages the Knowledge Base. It implements **Hybrid Search** (combining FAISS vector search and BM25 keyword search) and a **Small-to-Big retrieval strategy** to provide precise context to the LLM. |
| **`All_intents.py`** | **Business Logic.** Contains specific handler functions for each intent type (Calendar management, General Inquiries, HR requests, Administrative procedures, and User requests). It generates the final prompts for the LLM. |
| **`services.py`** | **External Services.** Handles interactions with Gmail (IMAP/SMTP) and Google Calendar. It manages drafting emails, reading inboxes, and syncing sent emails to the history log. |
| **`RulesForIntents.py`** | **Self-Learning Module.** Implements the "Process Mining" logic. It compares incoming emails with manual replies sent by the manager to deduce new administrative rules and updates the system's logic files dynamically. |

---

##  Key Features

* **Hybrid RAG System:** Combines semantic search (Embeddings) with keyword search (BM25) to retrieve accurate information from internal documents.
* **Arabic OCR Support:** Capable of reading scanned Arabic PDFs and images using `ArabicOcr`.
* **Smart Calendar Management:** Understands Gregorian and Hijri dates, handles relative time (e.g., "next Tuesday"), and checks Google Calendar availability.
* **Intent Classification:** Automatically categorizes emails into contexts like HR, Maintenance, Administrative, or Scheduling.
* **Continuous Learning:** The system monitors the "Sent" folder. If the manager manually replies to an email, the system analyzes the reply, extracts the rule used, and updates its own knowledge base for future automation.

##  Dependencies

The system relies on the following key libraries:
* `transformers` & `torch` (for LLM and Embeddings)
* `langchain` (for RAG and Vector Stores)
* `google-api-python-client` (for Gmail & Calendar)
* `ArabicOcr` (for image processing)
* `fitz` (PyMuPDF) & `openpyxl` (for file parsing)
* `hijri_converter` (for date handling)

##  How to Run

1.  Ensure all `requirements.txt` libraries are installed.
2.  Place your Google Service Account JSON and credentials in the root directory.
3.  Run the main script:
