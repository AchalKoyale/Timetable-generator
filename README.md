# 🎓 Smart Timetable Generator Web Application

> **Final-Year Engineering Mini-Project**  
> **Institution:** Mahatma Gandhi Mission's College of Engineering (MGM COE), Nanded  
> **Department:** Electronics and Telecommunication Engineering (E&TC)  
> **Academic Year:** 2026-27 (Semester-I)  
> **WEF Date:** 17/08/2026 | **Semester Start:** 10/08/2026  

---

## 🚀 Live Local Application Link

When running, the application is live at:
### 👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)** or **[http://localhost:5000](http://localhost:5000)**

---

## 🔑 Default Administrator Credentials

| Role | Username | Password | Access Level |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full Access (Edit, Generate, Reset, CRUD) |

---

## 🌟 Key Features

1. **Exact MGM COE Timetable Replica**:
   - Seeded with 100% authentic data from the uploaded college timetable PDF.
   - Separate timetables for all 3 classes:
     - **S.Y. (Second Year) – Semester 3**
     - **T.Y. (Third Year) – Semester 5**
     - **B.E. / Final Year – Semester 7**
   - Batches **S1, S2, S3, S4**, **T1, T2, T3, T4**, and **B1, B2, B3, B4**.
   - All 12 faculties with official codes: `DR.SLK`, `Dr.KPP`, `Dr.MRB`, `VSJ`, `PPK`, `SSA`, `AKS`, `MVM`, `DJT`, `ABD`, `KAP`, `SSP`.
   - All classrooms and laboratories: `F-12`, `F-13`, `F-14A (OC&ML)`, `F-14B (CP&CL)`, `F-17 (DEML)`, `F-18 (EDCL)`, `F-19 (CSL)`, `F-20 (ESVL/ESDL)`, `Lab 14 (PCBL)`, `Lab 14A (PCB&SL)`, `Online`.

2. **Editable Timetable Interface**:
   - Click on **any period cell** in the timetable to edit its details.
   - Modal interface allows changing:
     - Subject
     - Faculty
     - Classroom / Laboratory
     - Batch (Whole Class or S1/S2/S3/S4 etc.)
     - Session Type (Theory, Practical, Meeting, Online)
     - Custom Display Label
   - **Save Changes** updates the SQLite database instantly.
   - **Delete Entry** removes the period.
   - **Reset to PDF Schedule** button restores the official timetable from the PDF anytime.

3. **Intelligent Conflict & Clash Prevention**:
   - **Teacher Clash Prevention:** Prevents a teacher from being assigned to two classes at the same time.
   - **Class Clash Prevention:** Prevents a class from having two simultaneous whole-class lectures.
   - **Room / Lab Clash Prevention:** Prevents a room or lab from being double-booked.
   - **Live Clash Auditor:** Real-time auditor view showing 0 clashes (clean) or listing collision details with 1-click fixes.

4. **Multi-Perspective Views**:
   - **Master All-in-One View:** Exact replica of the college PDF layout.
   - **Class-wise Timetable:** Filtered specifically by S.Y., T.Y., or B.E.
   - **Faculty-wise Timetable:** Filtered by faculty member to see individual workload.
   - **Room/Lab Utilization View:** Shows occupancy and free slots for any room.

5. **Print & PDF Exporting**:
   - **Browser Print:** `@media print` styled for high-resolution A4 landscape printing.
   - **Server-side PDF Export:** Instant landscape PDF generation powered by ReportLab.
   - **CSV / Excel Export:** Download complete schedule for spreadsheets.

6. **Full CRUD Modules**:
   - Teachers & Faculty management
   - Subjects & Contact hours
   - Classes & Batches
   - Classrooms & Specialized Labs
   - Lecture timings, bell schedules, and recess breaks

---

## 🛠️ Technology Stack

- **Backend:** Python 3, Flask, Flask-SQLAlchemy, Werkzeug, ReportLab
- **Database:** SQLite (`timetable.db`)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, FontAwesome 6
- **Editor:** Visual Studio Code (VS Code)

---

## 💻 How to Run the Project in VS Code

### Step 1: Open the Project in VS Code
1. Open **VS Code**.
2. Go to **File** > **Open Folder...** and select the folder `shortcut tt`.

### Step 2: Open the Integrated Terminal
- Press `Ctrl + ~` (or go to **Terminal** > **New Terminal**).

### Step 3: Install Required Packages
Run the following command:
```powershell
py -3 -m pip install -r requirements.txt
```

### Step 4: Run the Application
Execute:
```powershell
py -3 app.py
```

### Step 5: Open in Your Browser
Visit:
```
http://127.0.0.1:5000
```
Log in using:
- **Username:** `admin`
- **Password:** `admin123`

---

## 📂 Project Architecture

```
shortcut tt/
│
├── app.py                     # Main Flask routes, APIs & server setup
├── models.py                  # Database Schema (SQLAlchemy Models)
├── seed_data.py               # Pre-loads exact authentic data from the PDF
├── generator.py               # Clash detection & automated generator engine
├── pdf_exporter.py            # ReportLab PDF generator matching college layout
├── requirements.txt           # Python dependencies
├── README.md                  # Complete documentation & project guide
│
├── static/
│   ├── css/
│   │   ├── style.css          # Modern dashboard styling & cell colors
│   │   └── print.css          # Print optimization for A4 landscape
│   └── js/
│       ├── main.js            # General UI interactions & mobile sidebar
│       └── timetable-editor.js# In-place cell click editing & conflict checker
│
└── templates/
    ├── base.html              # Base shell with sidebar, navbar & edit modal
    ├── login.html             # Admin authentication page
    ├── dashboard.html         # Executive overview & statistics
    ├── timetable_master.html  # Master Timetable (PDF replica)
    ├── timetable_class.html   # Class-wise schedule (SY, TY, BY)
    ├── timetable_teacher.html # Faculty personal schedule
    ├── timetable_room.html    # Classroom & Lab utilization view
    ├── conflict_report.html   # Clash detector & conflict audit matrix
    ├── generate.html          # Automated generator configuration
    ├── teachers.html          # Teacher CRUD management
    ├── subjects.html          # Subject CRUD management
    ├── classrooms.html        # Rooms & Labs CRUD management
    ├── classes.html           # Classes & Batches CRUD management
    └── timeslots.html         # Period timings & recess breaks
```
