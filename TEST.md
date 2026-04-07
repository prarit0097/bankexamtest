# TEST.md

## Is File Ka Purpose
Ye file is project ka easy guide hai. Isko aise likha gaya hai ki koi beginner, school student, ya non-technical person bhi padhkar samajh sake:

- project kya hai
- project kyu banaya gaya hai
- isme kya kya hota hai
- kaunsi files important hain
- ise kaise chalana hai
- iski strengths aur weaknesses kya hain

Simple line:
Ye file project ka "samjhaane wala notebook" hai.

---

## Project Ka Naam
Bank Exam Prep Platform

---

## Sabse Simple Explanation
Socho ek student bank exam ki tayari kar raha hai.
Usse baar baar test dene hain.
Usse dekhna hai:

- kitne answer sahi hue
- kitne galat hue
- galti kyu hui
- kis topic me weakness hai
- agle din tak progress kya rahi

Ye project wahi kaam karta hai.

Ye ek web app hai jahan student test de sakta hai aur app usko result, explanation, aur practice direction de sakta hai.

---

## Project Kya Karta Hai
Project ek online test platform banata hai jo banking exam students ke liye useful hai.

### Access Rule (Naya)
Ab app me login required hai. Bina login student/admin pages open nahi hongi.
Default seeded login:

- Username: `chahat@gmail.com`
- Password: `Chahat@123`

Student:
- mock test de sakta hai
- topic-wise test de sakta hai
- result dekh sakta hai
- sahi aur galat answer dekh sakta hai
- wrong answer ki explanation padh sakta hai
- weak area samajh sakta hai
- Telegram par daily summary pa sakta hai

Admin:
- papers upload kar sakta hai
- books ya PDFs upload kar sakta hai
- syllabus daal sakta hai
- questions review kar sakta hai
- explanations review kar sakta hai
- prediction practice sets generate kar sakta hai

---

## Project Kyu Banaya Gaya Hai
Bank exam preparation me students ko sirf padhna nahi, test practice bhi karni padti hai.

Problem:
- student ko regular tests nahi milte
- result detail me samajh nahi aata
- wrong answer ka reason clear nahi hota
- weak areas track nahi hote
- admin data upload kare bina platform kaam shuru nahi kar pata

Solution:
Ye project ek aisa app banata hai jo start se useful ho.

Matlab:
- agar admin ne abhi tak papers upload nahi kiye, tab bhi app kaam kare
- baad me real data aane par system aur strong ho jaye

---

## Ye Project Kis Exam Ke Liye Hai
Ye project India ke major banking exams ko dhyan me rakh kar banaya gaya hai.

Example:
- IBPS PO
- IBPS Clerk
- SBI PO
- SBI Clerk
- RBI Assistant
- NABARD Grade A

Future me aur exams bhi add kiye ja sakte hain.

---

## Student App Me Kya Hota Hai
Student side par ye major cheezein hoti hain:

### 1. Mock Test
Ye full practice test hota hai.
Student ko lagta hai jaise real exam jaisa test de raha hai.
Test chalne ke dauran live timer dikhta rehta hai, aur scroll karne par bhi timer sticky visible rehta hai.

### 2. Topic-wise Test
Agar student ko sirf ek topic practice karna hai, to vo topic-wise test le sakta hai.

Example:
- only puzzles
- only reading comprehension
- only arithmetic

### 3. Auto Checking
Test submit karne ke baad app khud answer check karta hai.

### 4. Score
App batata hai:
- total score
- correct count
- incorrect count
- skipped count
- test completion time (kitne time me test submit hua)

### 5. Explanation
Agar answer galat hai to app reason explain karta hai.

### 6. Weak Area Summary
App batata hai ki kaunsa topic weak hai.

### 7. Daily Telegram Report
Agar student ka Telegram linked hai, to last day ka report Telegram par bheja ja sakta hai.

### 8. Profile Page
Ab app me ek profile dashboard bhi hai.
Is page par student ka overall data dikh sakta hai:

- student name edit option
- total started tests
- total completed tests
- overall accuracy
- best accuracy
- weak areas
- strengths
- recent completed tests
- in-progress tests
- opportunities
- goals
- streaks

Important:
Student-facing pages par ab Telegram ki details show nahi ki jaati. Profile page par student apna visible name khud change kar sakta hai.

---

## Admin Side Me Kya Hota Hai
Admin project ke piche wala data control karta hai.

Admin kar sakta hai:
- paper upload
- PDF upload
- books upload
- syllabus upload
- content ingestion trigger
- question approval
- explanation edit
- prediction set review
- Telegram logs dekhna
- admin panel se quick overview aur action buttons use karna
- previous year papers upload karna
- test papers upload karna
- study materials upload karna
- upload ke baad app se exam/year/usage auto infer karwana
- ek hi batch me multiple files upload karna
- 50+ files ko backend batches me arrange karna
- batch summary ke through dekhna ki kaunse exams/years/usage buckets detect hue

Simple words:
Admin app ka teacher/control-room part hai.

---

## Bootstrap AI Mode Kya Hai
Ye is project ka bahut important idea hai.

Normal problem:
Agar admin ne abhi tak koi data upload nahi kiya, to test platform khaali ho jayega.

Is project ka solution:
App khud AI ki help se practice questions bana leta hai.

Isko kehte hain `Bootstrap AI Mode`.

Matlab:
- app start hote hi bekaar nahi hota
- admin data aane ka wait nahi karta
- student turant test de sakta hai

Important:
Ye generated questions backend me `generated` label ke saath save hote hain.
Student ko normal tarah se dikhte hain, lekin system ke andar pata hota hai ki ye AI-generated hain.

Isse future me difference samajhna easy hota hai:
- kaunsa question real source se aaya
- kaunsa question AI ne banaya

---

## RAG Mode Kya Hai
RAG ka simple matlab:
AI answer dene se pehle real uploaded material me relevant information dhoondta hai.

Agar admin ne:
- past papers
- books
- PDFs
- syllabus

upload kiya hai, to app unhe process karta hai.

Phir jab explanation chahiye hoti hai, system relevant material use karke better explanation de sakta hai.

Simple words:
Bootstrap mode me AI "khud soch kar" practice banata hai.
RAG mode me AI "uploaded material dekh kar" answer ya explanation improve karta hai.

---

## Prediction Feature Kya Hai
Project me prediction feature bhi hai.

Lekin important baat:
Ye exact future question guarantee nahi karta.

Ye sirf itna karta hai:
- pichle papers ke trends dekhta hai
- kaunse topics zyada repeat hote hain dekhta hai
- un trends ke basis par likely-question practice set banata hai

Simple words:
Ye bolta nahi "yehi question exam me aayega".
Ye bolta hai "in topics aur patterns ko practice karna smart hoga".

---

## App Ke Andar Data Kaise Chalta Hai
Bahut simple flow:

1. Exam, section, aur topic define hote hain
2. Questions system me store hote hain
3. Har question ke options hote hain
4. Ek option correct hota hai
5. Student test leta hai
6. Student answer submit karta hai
7. System score nikalta hai
8. Explanation attach hoti hai
9. Result save hota hai
10. Telegram summary ja sakti hai

---

## Is Project Me Kaun Kaun Se Data Types Hain
Project internally ye samajhta hai ki question kahaan se aaya:

- `generated` = AI ne banaya
- `verified-paper` = real paper se aaya
- `verified-book` = real book se aaya
- `verified-upload` = admin upload se aaya

Ye tracking important hai because:
- quality control hota hai
- admin filtering kar sakta hai
- future me migration easy hoti hai

---

## User Journey Example
Chalo ek simple example dekhte hain.

Ravi naam ka student app open karta hai.

Vo:
- exam choose karta hai: IBPS PO
- test type choose karta hai: mock test
- difficulty choose karta hai
- question count choose karta hai
- test start karta hai

Phir:
- app questions dikhaata hai
- Ravi answers deta hai
- submit karta hai
- app score nikalta hai
- wrong answers explain karta hai
- weak topic batata hai
- next day Telegram par summary bhej sakta hai

---

## Admin Journey Example
Ek admin ya teacher system me login karta hai.

Vo:
- PDF upload karta hai
- past paper upload karta hai
- content ingest karvata hai
- questions review karta hai
- prediction sets banvata hai

Isse student side quality dheere dheere better hoti jaati hai.

---

## Project Ka Structure Simple Language Me
Yahan kuch important files hain aur unka kaam kya hai:

- [README.md](/e:/coding/bank%20exam%20test/README.md)
  Ye quick intro aur setup guide hai.

- [AGENTS.md](/e:/coding/bank%20exam%20test/AGENTS.md)
  Ye future changes ke rules batata hai.

- [config/settings.py](/e:/coding/bank%20exam%20test/config/settings.py)
  Ye project ki settings file hai.

- [config/urls.py](/e:/coding/bank%20exam%20test/config/urls.py)
  Isme routes define hote hain.

- [prep/models.py](/e:/coding/bank%20exam%20test/prep/models.py)
  Isme database ke main objects defined hain.

- [prep/views.py](/e:/coding/bank%20exam%20test/prep/views.py)
  Student pages ka logic yahan hai.

- [templates/prep/admin_panel.html](/e:/coding/bank%20exam%20test/templates/prep/admin_panel.html)
  In-app admin dashboard yahan render hota hai.

- [prep/forms.py](/e:/coding/bank%20exam%20test/prep/forms.py)
  Test create karne ke form yahan hain.

- [prep/admin.py](/e:/coding/bank%20exam%20test/prep/admin.py)
  Admin panel customization yahan hai.

- [prep/services/assessment.py](/e:/coding/bank%20exam%20test/prep/services/assessment.py)
  Test banana, submit karna, score nikalna.

- [prep/services/bootstrap.py](/e:/coding/bank%20exam%20test/prep/services/bootstrap.py)
  Bootstrap AI mode ka logic.

- [prep/services/rag.py](/e:/coding/bank%20exam%20test/prep/services/rag.py)
  RAG explanation logic.

- [prep/services/prediction.py](/e:/coding/bank%20exam%20test/prep/services/prediction.py)
  Likely-question practice set generation.

- [prep/services/ingestion.py](/e:/coding/bank%20exam%20test/prep/services/ingestion.py)
  Uploaded files ko process karna.

- [prep/services/notifications.py](/e:/coding/bank%20exam%20test/prep/services/notifications.py)
  Telegram summary bhejna.

- [prep/tasks.py](/e:/coding/bank%20exam%20test/prep/tasks.py)
  Background tasks.

- [prep/tests.py](/e:/coding/bank%20exam%20test/prep/tests.py)
  Automated tests.

---

## Project Ka Tech Stack Simple Samjho

### Python
Main programming language.

### Django
Main web framework.
Isse app ki pages, database aur admin panel banaya gaya hai.

### Celery
Background jobs ke liye.
Jaise:
- ingestion
- Telegram report sending

### Redis
Celery ke saath queue/broker ki tarah use hota hai.

Important:
Large uploads ab background me queue hoti hain. Real async processing ke liye Celery worker run hona chahiye.

### PostgreSQL
Production database target.

### SQLite
Local simple development database.
Abhi dev mode me isi ko use kiya ja raha hai.

### OpenAI API
AI-generated questions, explanations, aur embeddings ke liye.

### Telegram Bot API
Daily reports bhejne ke liye.

### Backend Telegram Chat Control
Ab Telegram chat ID frontend form se nahi li jaati.
Ye backend se control hoti hai using:

- `DEFAULT_TELEGRAM_CHAT_ID`

Current dev backend chat ID:
- `712615667`

### PyPDF
PDF text read karne ke liye.

---

## Is Project Ki Achhi Baatein
- Start se useful hai, khaali app nahi banta
- Admin data aane se pehle bhi tests milte hain
- Student ko score + explanation dono milte hain
- Prediction practice available hai
- Internal tracking strong hai
- Future me upgrade karna easy hai
- Admin aur student dono ke flows soch kar banaya gaya hai

---

## Is Project Ki Limitations
- AI-generated questions kabhi kabhi imperfect ho sakte hain
- Abhi full vector database use nahi ho raha
- OCR nahi hai, image-only PDFs weak pad sakti hain
- Telegram onboarding full advanced flow nahi hai
- Prediction heuristic-based hai, trained ML model nahi
- Real production deployment abhi fully done nahi hai

---

## Project Ko Kaise Run Karein

### 1. Requirements install karo
```bash
python -m pip install -r requirements.txt
```

### 2. Environment file ready karo
```bash
copy .env.example .env
```

### 3. Database migrate karo
```bash
python manage.py migrate
```

### 4. Default exam taxonomy daalo
```bash
python manage.py seed_exam_taxonomy
```

### 5. App run karo
```bash
python manage.py runserver
```

### 5.1 Login karo
App open karne ke baad login page par default credentials use karo:

- Username: `chahat@gmail.com`
- Password: `Chahat@123`

### 6. Tests chalao
```bash
python manage.py test prep
```

### 7. Prediction sets generate karo
```bash
python manage.py generate_prediction_sets
```

### 8. Django health check
```bash
python manage.py check
```

### 9. Background ingestion worker (recommended)
```bash
celery -A config worker -l info
```

---

## Environment Variables Kya Hote Hain
Ye wo hidden configuration values hoti hain jo app ko chalane ke liye chahiye hoti hain.

Main values:
- `DJANGO_SECRET_KEY` = security key
- `DJANGO_DEBUG` = debug mode on/off
- `DJANGO_ALLOWED_HOSTS` = app kin hosts par chalega
- `DATABASE_URL` = database connection
  Dev mode me current value: `sqlite:///db.sqlite3`
- `CELERY_BROKER_URL` = Celery broker
- `CELERY_RESULT_BACKEND` = Celery result backend
- `OPENAI_API_KEY` = AI access key
- `OPENAI_MODEL` = kaunsa model use hoga
- `OPENAI_EMBEDDING_MODEL` = embeddings model
- `TELEGRAM_BOT_TOKEN` = Telegram bot access
- `DEFAULT_TELEGRAM_CHAT_ID` = backend se fixed Telegram chat routing
- `DATA_UPLOAD_MAX_NUMBER_FILES` = ek request me kitni files upload ho sakti hain
- `DATA_UPLOAD_MAX_MEMORY_SIZE` = poori upload request ka max size bytes me
- `FILE_UPLOAD_MAX_MEMORY_SIZE` = ek file ko memory me rakhne ki limit bytes me

Important:
Real secrets ko public file me nahi rakhna chahiye.
App startup par `.env` file automatically load hoti hai, isliye local dev me values alag se manually export karna zaroori nahi hai.

---

## Project Abhi Kitna Verified Hai
Ye commands successfully chal chuki hain:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py migrate`
- `python manage.py test prep`
- `python manage.py seed_exam_taxonomy`
- `python manage.py generate_prediction_sets`

Matlab:
Basic project structure, migrations, aur core flows test ho chuke hain.

---

## Future Me Kya Better Ho Sakta Hai
- Better UI/UX
- Hindi language support
- Better Telegram onboarding
- OCR support for scanned PDFs
- Better retrieval system
- Real vector database
- Better prediction model
- More admin analytics
- Student login history and long-term dashboard

---

## Important Warnings
- `.env.example` me kabhi real API keys nahi honi chahiye
- AI-generated content ko hamesha high-confidence truth nahi maana ja sakta
- Prediction feature ko guarantee ke roop me market nahi karna chahiye
- Real papers aur copyrighted books use karte waqt licensing clear honi chahiye

---

## Short Summary For Anyone
Agar koi ek line me pooche:

Ye project ek smart banking-exam test platform hai jo student ko test, score, explanation, weak-area analysis, prediction-based practice aur Telegram report deta hai. Aur sabse important baat: admin data upload karne se pehle bhi AI ke through chalu ho sakta hai.

---

## Change Log
### 2026-04-06
- Django project scaffold create kiya
- Banking exam taxonomy, models, admin, services, templates, tasks aur tests add kiye
- `.env` create kiya aur generated `DJANGO_SECRET_KEY` set ki
- Telegram bot token validate kiya
- `TEST.md` aur `AGENTS.md` documentation rules add kiye
- `TEST.md` ko beginner-friendly aur much more explainable format me rewrite kiya
- Dev mode database ko SQLite par switch kiya
- Global rule reinforce kiya gaya ki har future change se pehle `AGENTS.md` read karna mandatory hai
- `.env.example` se real Telegram token hata kar placeholder state maintain ki gayi
- `.omx/` local state ko remote push se bachane ke liye `.gitignore` update kiya gaya
- App settings me `.env` auto-loading add ki gayi taaki local secrets/config actual Django runtime me use ho sake
- Telegram send flow ko strict banaya gaya taaki Telegram API `ok=false` responses ko success mark na kiya jaye
- Automated tests ko isolate kiya gaya taaki test suite real OpenAI aur Telegram network calls par depend na kare
- `.venv/` ko `.gitignore` me add kiya gaya taaki local virtual environment remote me push na ho
- Telegram chat ID ko backend-controlled banaya gaya aur frontend form se hata diya gaya
- Test creation form me section/topic filtering aur clearer invalid-selection feedback add ki gayi, taaki `Generate test session` click par silent failure na lage
- Result page me navigation add ki gayi: dashboard par wapas jaane aur similar test dobara start karne ke options
- Student profile dashboard add kiya gaya jisme performance summary, weak areas, strengths, opportunities, goals, recent tests aur in-progress tests dikhte hain
- Student name change option add kiya gaya aur visible pages se Telegram-related text hata diya gaya
- Profile page ko visually refine kiya gaya with stronger dashboard styling and `Edit name` interaction after save
- Shared top navigation bar add ki gayi jisme dashboard, start new test, aur profile links har main page par visible hain
- Shared nav aur home page me `Predicted Papers` section add ki gayi jahan sare exams ke future predicted paper drafts dikhte hain
- `OPENAI_MODEL` ko `gpt-4o-mini` par update kiya gaya
- Navbar se `Bank Exam Prep / Jeena Sikho` brand text remove kiya gaya, ab sirf clean navigation links dikhte hain
- App scan ke basis par in-app admin panel add kiya gaya jahan se platform overview, quick actions, recent assets, recent tests, prediction sets, aur deep Django admin links access kiye ja sakte hain
- Admin panel ke major options ko dedicated in-app admin section pages se connect kiya gaya, taaki click karne par proper result page khule
- End-user admin UX me saare visible Django admin links/buttons remove kiye gaye; ab sirf in-app admin pages dikhte hain
- Admin panel me 3 structured upload flows add kiye gaye: previous year papers, test papers, aur study materials; upload ke baad app auto-scan karke exam, year, aur recommended usage infer karta hai
- Bulk upload intelligence add ki gayi: ek hi upload me multiple files process hoti hain, upload batch banta hai, exam/year/bucket distribution summarize hota hai, aur app ko samajh aata hai ki in documents ko backend me kaise organize karna hai
- Bulk upload forms me live progress UI add ki gayi: upload ke dauran progress bar aur percentage dikhte hain, aur server processing phase me status text update hota hai
- Har upload section ke saath reset button add kiya gaya; confirm karne par sirf us category ka data delete hota hai aur baaki categories safe rehti hain
- Reset ke baad `Recent Upload Batches / Bulk arrangement summaries` me audit-style entry aati hai jo batati hai ki us section ka data remove ho gaya
- Admin ke 3 upload cards me ab current uploaded file count dikhaya जाता hai; zero hone par bhi `0` visible rehta hai
- Legacy uploaded files ko bhi section counts aur reset logic me include kiya gaya, taki purana data aur naya data dono same admin controls se manage ho sake
- Reset UX improve ki gayi: ab reset ke baad success prompt aata hai aur page force reload hoti hai, taaki latest count user ko turant dikh sake
- Admin panel response ko no-cache banaya gaya aur reset XHR ab updated counts return karta hai, taaki browser stale `151` count na dikhaye
- Admin upload JS me form action collision bug fix kiya gaya; ab single upload aur reset dono sahi route par jaate hain aur `[object RadioNodeList]` path error nahi aata
- Markdown (`.md`) files bhi upload pipeline me first-class supported hain; forms, validation, ingestion aur metadata inference unke saath bhi kaam karte hain
- Prediction flow ko OpenAI-assisted banaya gaya: prediction set generation ab likely paper title, summary, likely pattern, aur focus areas AI ke through enrich kar sakti hai; fallback logic bhi present hai
- Predicted Papers page me cards clickable banaye gaye; click karne par full predicted paper detail khulta hai jahan sare predicted questions list hote hain
- Predicted paper detail ko real-paper style me improve kiya gaya: section grouping, full question list, likely answer highlighting, aur weak placeholder `[AI Practice]` items ko filter karne ki logic add ki gayi
- Old generated placeholder stems ko bhi predicted paper detail view se explicitly hide kiya gaya, taki purane stored sets me bhi fake-looking questions na dikhen
- Bulk uploads ke liye Django upload limits raise ki gayi, taki 135 jaise large multi-file uploads `TooManyFilesSent` error na den

### 2026-04-07
- App-wide login system add kiya gaya; unauthenticated user ab protected pages access nahi kar sakta
- Default seeded login user add kiya gaya: `chahat@gmail.com` / `Chahat@123`
- Upload ingestion ko request path se hata kar async task queue par shift kiya gaya, taki large uploads UI request ko block na karein
- Upload validation tighten ki gayi: `.docx` supported, legacy `.doc` reject hoti hai (convert to `.docx`)
- Ingestion layer me real `.docx` text extraction add ki gayi (`word/document.xml` parsing)
- `OPENAI_MODEL` default mismatch fix kiya gaya (`settings.py` aur `.env.example` aligned to `gpt-4o-mini`)
- Predicted Papers page par `Exams covered` metric ko unique exam count par correct kiya gaya
- Test session page me live sticky countdown timer add kiya gaya jo scroll ke dauran bhi visible rehta hai
- Timer zero hone par test auto-submit behavior add kiya gaya
- Student `Submit test` click karte hi timer immediately freeze hota hai, taaki completion time submit moment se clearly capture ho
- Result Summary me test completion time show kiya gaya
- Profile dashboard me average completion time aur each recent completed test ka completion time show kiya gaya
- `_get_assets_for_category` ko DB-level queryset filtering par optimize kiya gaya; ab saare assets memory me load nahi hote, sirf matching records database se aate hain
- Thread-based ingestion fallback me retry mechanism add kiya gaya (3 attempts with exponential backoff); failures ab properly log hote hain
- Admin section views me pagination add ki gayi (25 items per page); First/Previous/Next/Last navigation controls ke saath
- `_naive_embedding` ko 1536 dimensions par upgrade kiya gaya taaki OpenAI embedding dimensions ke saath compatible ho; output ab L2-normalized hota hai
- PDF text extraction me empty text warning log add kiya gaya; scanned/image-only PDFs ka OCR gap clearly logged hota hai
- `ensure_default_taxonomy()` me in-memory cache add kiya gaya taaki har request par unnecessary DB query na ho; test suite me cache reset logic bhi add ki gayi
- OpenAI API calls me 1-second throttle add kiya gaya taaki rapid-fire requests se rate limit hit na ho
- Test creation me 5-second cooldown add kiya gaya taaki accidental double-click se duplicate sessions na bane
- Prediction engine ko completely rewrite kiya gaya: ab har exam ke har section ke liye AI se real exam-style MCQ questions generate hote hain (5 per section)
- Prediction questions ab placeholder nahi hain; actual banking exam difficulty ke questions hain jaise Quantitative Aptitude me real calculations, Reasoning me puzzles, English me grammar/vocabulary, aur Banking Awareness me factual questions
- Jab OpenAI API available hai tab AI research-based questions aate hain; jab nahi hai tab smart fallback templates use hote hain jo actual exam patterns follow karte hain
- Uploaded corpus data (study materials, papers) bhi prediction question generation me context ke roop me use hota hai (RAG-style)
- Predicted paper detail page me section-wise grouping aur correct answer highlighting improve ki gayi
