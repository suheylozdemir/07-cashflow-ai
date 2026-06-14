# CashFlow AI 💼
🚀 **[Live Demo](https://07-cashflow-ai-jrrxgivijfe7cmc9tmpqwx.streamlit.app/)**
AI-powered GST classification and cash flow analysis for Australian small businesses. Upload your bank statement CSV and get an instant BAS summary, 90-day cash flow forecast, and spending anomaly detection — all powered by real ATO documentation.

---

## The Problem

Every quarter, Australian small businesses face the same painful process: manually sorting through hundreds of bank transactions, deciding which are GST-applicable and which are exempt, calculating the net GST owed to the ATO, and submitting their Business Activity Statement (BAS). Most businesses pay accountants AUD 300–500 per quarter just for this task. The rules are complex — basic food is GST-free, but a prepared meal is not. Payroll has no GST, but a contractor invoice does.

CashFlow AI automates this entirely.

---

## What It Does

Upload a CSV bank statement. The system does three things:

**1. AI-Powered GST Classification**
Every transaction is classified against official ATO GST rules. The system uses RAG — retrieval-augmented generation — to ground each decision in real ATO documentation fetched from ato.gov.au. It does not rely on the model's own knowledge. Each classification comes with a confidence level (High/Medium/Low) and the specific ATO rule that applies.

**2. BAS Summary Generation**
From the classified transactions, the system automatically calculates everything needed for a BAS lodgement: total taxable sales, GST-free sales, GST collected, GST paid on expenses, and the net GST owed to the ATO. The output mirrors the exact fields on the ATO's BAS form.

**3. Cash Flow Forecast + Anomaly Detection**
Using 90 days of historical transaction data, the system projects the next 90 days of cash flow. Separately, an IsolationForest ML model detects spending anomalies — transactions that deviate significantly from their category average. A parking expense that is 50% higher than usual, a supplier invoice that doubled — these are flagged with severity levels.

---

## Architecture

```
User uploads CSV bank statement
          │
          ▼
    Streamlit UI
          │
          ▼
   GST Agent (LangChain + OpenAI)
          │
    ┌─────┴──────┐
    ▼            ▼
Pinecone      GPT-4.1-mini
(ATO Rules)   (Classification)
          │
          ▼
   Classified DataFrame
          │
    ┌─────┴──────────┐
    ▼                ▼
BAS Summary    Forecaster + IsolationForest
                    │
                    ▼
              Streamlit Dashboard
              (4 tabs: Overview, Cash Flow,
               GST & BAS, Anomalies)
```

---

## Key Technical Decisions

**Why RAG for GST classification?**
GST rules are specific, frequently updated, and consequential — a wrong classification means ATO penalties. Grounding the model in real ATO documentation via RAG eliminates hallucination risk on tax rules. Every classification is traceable to a source URL.

**Why IsolationForest for anomalies instead of LLM?**
Anomaly detection is a statistical problem, not a language problem. IsolationForest identifies outliers within each spending category using unsupervised learning — no labels needed, no API cost, sub-second inference. Using an LLM here would be slower, more expensive, and no more accurate.

**Why batch processing for classification?**
Sending each transaction as a separate API call would be slow and expensive. The system batches 10 transactions per GPT call, reducing API calls by 10x and cutting cost and latency proportionally.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| GST Classification | OpenAI gpt-4.1-mini + RAG |
| ATO Rules Database | Pinecone (10 ATO pages indexed) |
| Anomaly Detection | scikit-learn IsolationForest |
| Cash Flow Forecast | Pandas + statistical projection |
| UI | Streamlit |
| Data Generation | Faker (en_AU locale) |
| CI/CD | GitHub Actions |

---

## How to Run

**1. Clone the repo**

```bash
git clone https://github.com/suheylozdemir/07-cashflow-ai
cd 07-cashflow-ai
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Set up environment variables**

```bash
cp .env.example .env
# Add OPENAI_API_KEY, PINECONE_API_KEY, TAVILY_API_KEY
```

**4. Index ATO documentation into Pinecone**

```bash
python -c "from app.rag import index_ato_documents; index_ato_documents()"
```

**5. Generate sample bank statement**

```bash
python app/generate_mock_data.py
```

**6. Start the app**

```bash
streamlit run ui/streamlit_app.py
```

**7. Run tests**

```bash
pytest tests/ -v
```

---

## Sample Output

**Input:** `bank_statement_Q1_2026.csv` — 132 transactions, Sydney Tech Solutions Pty Ltd

**BAS Summary:**
- Total Sales: AUD 251,063.67
- GST Collected: AUD 22,823.98
- GST Paid: AUD 3,677.71
- Net GST Owed to ATO: AUD 19,146.27

**Anomalies detected:** 7 (2 High severity, 5 Medium)
- Woolworths Office Supplies: AUD 284.16 (+104% above average)
- Uber Business Travel: AUD 144.92 (+53% above average)

---

## Extending to Production

The current system uses a mock dataset generated with realistic Sydney business data. In production, this connects directly to:

- **Open Banking API** — real-time bank feed via CDR (Consumer Data Right), Australia's open banking standard
- **Xero or MYOB API** — direct integration with existing accounting software
- **ATO's SBR (Standard Business Reporting)** — automated BAS lodgement directly from the system

The RAG pipeline is already production-ready — it indexes live ATO pages and can be re-indexed whenever ATO updates its rules.

---

## Türkçe Açıklama

Avustralya'daki küçük işletmeler için yapay zeka destekli GST sınıflandırma ve nakit akışı analiz aracı. Banka ekstresi CSV'si yüklenir, sistem anında BAS özeti, 90 günlük nakit akışı tahmini ve harcama anomali tespiti üretir.

## Problem

Her çeyrekte Avustralyalı küçük işletme sahipleri aynı süreci yaşıyor: yüzlerce banka işlemini manuel olarak tarayıp hangisinin GST'ye tabi hangisinin muaf olduğuna karar veriyorlar, ATO'ya ödenecek net GST'yi hesaplıyorlar ve BAS formunu dolduruyorlar. Çoğu işletme bu iş için muhasebeciye çeyrek başına 300–500 AUD ödüyor. Kurallar karmaşık: temel gıda GST'siz ama hazır yemek değil. Maaş ödemesinde GST yok ama taşeron faturasında var.

CashFlow AI bu süreci tamamen otomatize ediyor.

## Nasıl Çalışır?

**1. GST Sınıflandırması**
Her işlem, ato.gov.au'dan çekilen resmi ATO dökümanlarına dayanarak sınıflandırılıyor. Model kendi bilgisini değil, RAG pipeline üzerinden erişilen gerçek ATO içeriğini kullanıyor. Her karar için güven seviyesi ve uygulanan ATO kuralı gösteriliyor. Bu yaklaşım hallucination riskini sıfıra indiriyor — vergi konusunda bu kritik.

**2. BAS Özeti**
Sınıflandırılmış işlemlerden BAS formu için gereken tüm rakamlar otomatik hesaplanıyor: vergilendirilebilir satışlar, GST'siz satışlar, tahsil edilen GST, giderlerde ödenen GST ve ATO'ya ödenecek net GST. Çıktı ATO'nun BAS formundaki alanlarla birebir örtüşüyor.

**3. Nakit Akışı Tahmini ve Anomali Tespiti**
90 günlük geçmiş veriye bakılarak önümüzdeki 90 gün için nakit akışı tahmini yapılıyor. Ayrı olarak scikit-learn'ün IsolationForest algoritması her kategori içindeki anormal harcamaları tespit ediyor. Normalden %50 yüksek bir enerji faturası, ikiye katlanan bir tedarikçi ödemesi — bunlar High veya Medium severity ile işaretleniyor.

## Teknik Kararlar

**Neden GST için RAG?**
GST kuralları spesifik, sık güncellenen ve sonuçları önemli. Yanlış sınıflandırma ATO cezası demek. Modeli resmi ATO dökümanına dayandırmak hallucination riskini ortadan kaldırıyor. Her karar kaynak URL'e izlenebilir.

**Neden anomali için IsolationForest, LLM değil?**
Anomali tespiti istatistiksel bir problem, dil problemi değil. IsolationForest her harcama kategorisinde aykırı değerleri denetimsiz öğrenmeyle buluyor. API maliyeti yok, label gerekmez, milisaniyede sonuç. LLM kullanmak daha yavaş, daha pahalı ve daha az güvenilir olurdu.

**Neden batch processing?**
Her işlemi ayrı API call olarak göndermek yavaş ve pahalı. Sistem 10 işlemi tek GPT call'unda gönderiyor, API maliyetini ve süreyi 10 kat azaltıyor.

## Teknoloji Stack

- **GST Sınıflandırması:** OpenAI gpt-4.1-mini + RAG (10 ATO sayfası Pinecone'da indexli)
- **Anomali Tespiti:** scikit-learn IsolationForest — denetimsiz öğrenme, label gerektirmez
- **Nakit Akışı:** Pandas tabanlı istatistiksel projeksiyon
- **UI:** Streamlit — 4 sekme: Overview, Cash Flow, GST & BAS, Anomalies
- **Veri Üretimi:** Faker (en_AU locale) — Sydney işletmelerine özgü gerçekçi mock data
- **CI/CD:** GitHub Actions — her push'ta otomatik test

## Production'a Genişletme

Mevcut sistem gerçekçi Sydney işletme verisiyle üretilmiş mock dataset kullanıyor. Production'da şunlara bağlanabilir:

- **Open Banking API** — CDR (Consumer Data Right) üzerinden gerçek zamanlı banka feed'i
- **Xero veya MYOB API** — mevcut muhasebe yazılımıyla direkt entegrasyon
- **ATO SBR (Standard Business Reporting)** — sistemden direkt BAS gönderimi

RAG pipeline zaten production-ready: canlı ATO sayfalarını indexliyor, ATO kuralları güncellenince tek komutla yeniden indexlenebilir.