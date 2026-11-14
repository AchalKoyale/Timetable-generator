import os
import sqlite3
from models import db, User, Teacher, Room, AcademicClass, Batch, Subject, TimeSlot, TimetableEntry, CollegeSetting, TeacherWorkloadAssignment

def migrate_database():
    """Ensure database schema is up-to-date with new columns without data loss."""
    db_paths = [
        os.path.join(os.path.dirname(__file__), 'instance', 'timetable.db'),
        os.path.join(os.path.dirname(__file__), 'timetable.db')
    ]
    for path in db_paths:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(teachers)")
                cols = [c[1] for c in cursor.fetchall()]
                if 'max_daily_lectures' not in cols:
                    cursor.execute("ALTER TABLE teachers ADD COLUMN max_daily_lectures INTEGER DEFAULT 3")
                if 'day_off' not in cols:
                    cursor.execute("ALTER TABLE teachers ADD COLUMN day_off TEXT")
                if 'is_available' not in cols:
                    cursor.execute("ALTER TABLE teachers ADD COLUMN is_available BOOLEAN DEFAULT 1")
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Migration note for {path}: {e}")

def seed_database():
    migrate_database()
    db.create_all()

    # 1. College Setting
    setting = CollegeSetting.query.first()
    if not setting:
        setting = CollegeSetting(
            trust_name="Mahatma Gandhi Mission's",
            college_name="COLLEGE OF ENGINEERING",
            address="Near Airport, Off Hingoli Road, Nanded-431605. (An Autonomous Institute, Accredited by NAAC & NBA)",
            department_name="DEPARTMENT OF ELECTRONICS AND TELECOMMUNICATION ENGINEERING",
            academic_year="ACADEMIC YEAR 2026-27 (SEMESTER-I) TIME TABLE",
            sem_start_date="10/08/2026",
            wef_date="17/08/2026",
            tt_incharge="Mr. Sayed Shoaib Anwar",
            dept_coordinator="Ms. A. K. Salve",
            hod_name="Dr. Mrs. Kalpana P. Paithane"
        )
        db.session.add(setting)

    # 2. Admin User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

    # 3. Faculty List (Exact 12 Teachers from the PDF)
    faculties_data = [
        {"name": "Dr. Mr. S. L. KOTGIRE", "code": "DR.SLK", "designation": "Vice Principal / Associate Professor", "email": "slkotgire@mgmcen.ac.in", "max_hours": 3},
        {"name": "Dr. Mrs. K. P. PAITHANE", "code": "Dr.KPP", "designation": "Professor & Head of Department", "email": "kppaithane@mgmcen.ac.in", "max_hours": 14},
        {"name": "Dr. M. R. BANWASKAR", "code": "Dr.MRB", "designation": "Assistant Professor / NBA Criteria 03", "email": "mrbanwaskar@mgmcen.ac.in", "max_hours": 14},
        {"name": "Mr. V. S. JADHAV", "code": "VSJ", "designation": "Assistant Professor / Dept. NBA Coordinator", "email": "vsjadhav@mgmcen.ac.in", "max_hours": 19},
        {"name": "Ms. P. P. KANADKHEDKAR", "code": "PPK", "designation": "Assistant Professor / Class Incharge TY", "email": "ppkanadkhedkar@mgmcen.ac.in", "max_hours": 21},
        {"name": "Mr. SAYED SHOAIB ANWAR", "code": "SSA", "designation": "Assistant Professor / Time Table Incharge", "email": "ssanwar@mgmcen.ac.in", "max_hours": 20},
        {"name": "Ms. A. K. SALVE", "code": "AKS", "designation": "Assistant Professor / Dept. Academic Coordinator", "email": "aksalve@mgmcen.ac.in", "max_hours": 21},
        {"name": "Ms. MAITHILI V. M.", "code": "MVM", "designation": "Assistant Professor / Class Incharge B.Tech", "email": "mvmaithili@mgmcen.ac.in", "max_hours": 20},
        {"name": "Mr. D. J. TUPTEWAR", "code": "DJT", "designation": "Assistant Professor / NBA Criteria 04", "email": "djtuptewar@mgmcen.ac.in", "max_hours": 21},
        {"name": "Ms. A. B. DALVI", "code": "ABD", "designation": "Assistant Professor / Girls Hostel Incharge", "email": "abdalvi@mgmcen.ac.in", "max_hours": 21},
        {"name": "Ms. KUCHAN A. P.", "code": "KAP", "designation": "Assistant Professor", "email": "apkuchan@mgmcen.ac.in", "max_hours": 22},
        {"name": "Dr. S. S. PATIL", "code": "SSP", "designation": "Assistant Professor (Maths)", "email": "sspatil@mgmcen.ac.in", "max_hours": 16}
    ]

    teacher_map = {}
    for f in faculties_data:
        t = Teacher.query.filter_by(code=f["code"]).first()
        if not t:
            t = Teacher(
                name=f["name"],
                code=f["code"],
                designation=f["designation"],
                email=f["email"],
                department="Electronics and Telecommunication Engineering",
                max_weekly_hours=f["max_hours"],
                max_daily_lectures=3
            )
            db.session.add(t)
            db.session.flush()
        else:
            t.max_weekly_hours = f["max_hours"]
        teacher_map[t.code] = t

    # 4. Rooms and Laboratories from PDF
    rooms_data = [
        {"name": "F-12", "short_code": "F-12", "room_type": "Classroom", "capacity": 75},
        {"name": "F-13", "short_code": "F-13", "room_type": "Classroom", "capacity": 75},
        {"name": "F-14", "short_code": "CPSL", "room_type": "Laboratory", "capacity": 30},
        {"name": "F-14A", "short_code": "OC&ML", "room_type": "Laboratory", "capacity": 30},
        {"name": "F-14B", "short_code": "CP&CL", "room_type": "Laboratory", "capacity": 30},
        {"name": "F-17", "short_code": "DEML", "room_type": "Laboratory", "capacity": 30},
        {"name": "F-18", "short_code": "EDCL", "room_type": "Laboratory", "capacity": 30},
        {"name": "F-19", "short_code": "CSL", "room_type": "Laboratory", "capacity": 30},
        {"name": "F-20", "short_code": "ESVL/ESDL", "room_type": "Laboratory", "capacity": 30},
        {"name": "Lab 14", "short_code": "PCBL", "room_type": "Laboratory", "capacity": 30},
        {"name": "Lab 14A", "short_code": "PCB&SL", "room_type": "Laboratory", "capacity": 30},
        {"name": "Online", "short_code": "VIRTUAL", "room_type": "Classroom", "capacity": 120}
    ]

    room_map = {}
    for r in rooms_data:
        rm = Room.query.filter_by(name=r["name"]).first()
        if not rm:
            rm = Room(name=r["name"], short_code=r["short_code"], room_type=r["room_type"], capacity=r["capacity"])
            db.session.add(rm)
            db.session.flush()
        room_map[rm.name] = rm

    # 5. Classes and Batches (SY, TY, BY, FY, A&R, Mech)
    classes_data = [
        {"name": "SY(ECT)", "year_name": "Second Year (NEP 2020)", "semester": 3, "batches": [("S1", "1-20"), ("S2", "21-40"), ("S3", "41-60"), ("S4", "61 Onwards")]},
        {"name": "TY(ECT)", "year_name": "Third Year", "semester": 5, "batches": [("T1", "1-20"), ("T2", "21-40"), ("T3", "41-60"), ("T4", "61 Onwards")]},
        {"name": "BY(ECT)", "year_name": "Final Year / B.Tech", "semester": 7, "batches": [("B1", "1-20"), ("B2", "21-40"), ("B3", "41-60"), ("B4", "61 Onwards")]},
        {"name": "FY(MGM)", "year_name": "First Year", "semester": 1, "batches": [("F1", "1-30"), ("F2", "31-60")]},
        {"name": "SY-A&R", "year_name": "Second Year (A&R)", "semester": 3, "batches": [("AR1", "1-30"), ("AR2", "31-60")]},
        {"name": "BY-Mech", "year_name": "Final Year (Mechanical)", "semester": 7, "batches": [("M1", "1-30"), ("M2", "31-60")]}
    ]

    class_map = {}
    batch_map = {}
    for c in classes_data:
        cls = AcademicClass.query.filter_by(name=c["name"]).first()
        if not cls:
            cls = AcademicClass(
                name=c["name"],
                year_name=c["year_name"],
                semester=c["semester"],
                department="Electronics and Telecommunication Engineering"
            )
            db.session.add(cls)
            db.session.flush()
        class_map[cls.name] = cls

        for b_name, b_range in c["batches"]:
            b = Batch.query.filter_by(class_id=cls.id, name=b_name).first()
            if not b:
                b = Batch(class_id=cls.id, name=b_name, roll_range=b_range)
                db.session.add(b)
                db.session.flush()
            batch_map[b_name] = b

    # 6. Time Slots matching the PDF Header
    slots_data = [
        {"slot_index": 1, "start_time": "08:00", "end_time": "10:00", "slot_label": "08:00 TO 09:00 Or 10:00", "is_recess": False},
        {"slot_index": 2, "start_time": "10:00", "end_time": "10:30", "slot_label": "10:00 TO 10:30 (Recess)", "is_recess": True, "recess_label": "Recess"},
        {"slot_index": 3, "start_time": "10:30", "end_time": "11:30", "slot_label": "10:30 TO 11:30", "is_recess": False},
        {"slot_index": 4, "start_time": "11:30", "end_time": "12:30", "slot_label": "11:30 TO 12:30", "is_recess": False},
        {"slot_index": 5, "start_time": "12:30", "end_time": "01:00", "slot_label": "12:30 TO 01:00 (Lunch Break)", "is_recess": True, "recess_label": "Recess / Lunch"},
        {"slot_index": 6, "start_time": "01:00", "end_time": "02:00", "slot_label": "01:00 TO 02:00", "is_recess": False},
        {"slot_index": 7, "start_time": "02:00", "end_time": "03:00", "slot_label": "02:00 TO 03:00", "is_recess": False},
        {"slot_index": 8, "start_time": "03:00", "end_time": "03:30", "slot_label": "03:00 TO 03:30 (Recess)", "is_recess": True, "recess_label": "Recess"},
        {"slot_index": 9, "start_time": "03:30", "end_time": "04:30", "slot_label": "03:30 To 04:30", "is_recess": False},
        {"slot_index": 10, "start_time": "04:30", "end_time": "05:30", "slot_label": "04:30 TO 05:30", "is_recess": False}
    ]

    slot_map = {}
    for s in slots_data:
        ts = TimeSlot.query.filter_by(slot_index=s["slot_index"]).first()
        if not ts:
            ts = TimeSlot(
                slot_index=s["slot_index"],
                start_time=s["start_time"],
                end_time=s["end_time"],
                slot_label=s["slot_label"],
                is_recess=s["is_recess"],
                recess_label=s.get("recess_label")
            )
            db.session.add(ts)
            db.session.flush()
        slot_map[ts.slot_index] = ts

    # 7. Subjects Catalog
    subjects_data = [
        # S.Y. (ECT) - Sem 3
        {"code": "TH-BSC-EM-III-201", "name": "Engineering Mathematics-III", "type": "Theory", "class": "SY(ECT)", "teacher": "SSP", "room": "F-12", "hours": 4},
        {"code": "TH-PCC-EDC-202", "name": "Electronic Devices & Circuits", "type": "Theory", "class": "SY(ECT)", "teacher": "DJT", "room": "F-12", "hours": 4},
        {"code": "TH-PCC-NT-203", "name": "Network Theory", "type": "Theory", "class": "SY(ECT)", "teacher": "DR.SLK", "room": "F-12", "hours": 3},
        {"code": "TH-OEI-PDE-233", "name": "Partial Differential Equations", "type": "Theory", "class": "SY(ECT)", "teacher": "ABD", "room": "F-12", "hours": 3},
        {"code": "TH-HSSM-ED-232", "name": "Entrepreneurship Development", "type": "Theory", "class": "SY(ECT)", "teacher": "Dr.MRB", "room": "F-12", "hours": 2},
        {"code": "TH-VEC-CoI-231", "name": "Constitution of India", "type": "Theory", "class": "SY(ECT)", "teacher": "Dr.KPP", "room": "F-12", "hours": 2},
        {"code": "TH-PCCL-SL-207", "name": "Skill Lab Theory", "type": "Theory", "class": "SY(ECT)", "teacher": "SSA", "room": "F-12", "hours": 1},
        {"code": "TH-MDM-IoT-Online", "name": "Multidisciplinary Minor - IoT", "type": "Online", "class": "SY(ECT)", "teacher": "SSA", "room": "F-13", "hours": 4},
        {"code": "PR-EDC", "name": "Electronic Devices & Circuits Lab", "type": "Practical", "class": "SY(ECT)", "teacher": "DJT", "room": "F-18", "hours": 8},
        {"code": "PR-NT", "name": "Network Theory Lab", "type": "Practical", "class": "SY(ECT)", "teacher": "MVM", "room": "F-19", "hours": 8},
        {"code": "PR-SL", "name": "Skill Lab Practical", "type": "Practical", "class": "SY(ECT)", "teacher": "SSA", "room": "F-20", "hours": 8},
        {"code": "PR-MProj", "name": "Mini Project Lab", "type": "Practical", "class": "SY(ECT)", "teacher": "PPK", "room": "F-14B", "hours": 8},

        # T.Y. (ECT) - Sem 5
        {"code": "TH-PCC-EWT", "name": "Electromagnetic Waves & Transmission", "type": "Theory", "class": "TY(ECT)", "teacher": "MVM", "room": "F-13", "hours": 4},
        {"code": "TH-PEC-FoC", "name": "Fundamentals of Communication", "type": "Theory", "class": "TY(ECT)", "teacher": "PPK", "room": "F-13", "hours": 3},
        {"code": "TH-PPC-DSP", "name": "Digital Signal Processing", "type": "Theory", "class": "TY(ECT)", "teacher": "Dr.KPP", "room": "F-12", "hours": 4},
        {"code": "TH-PCC-AC", "name": "Analog Communication", "type": "Theory", "class": "TY(ECT)", "teacher": "SSA", "room": "F-12", "hours": 3},
        {"code": "TH-OE-XYZ", "name": "Open Elective (OE-XYZ / OEB)", "type": "Theory", "class": "TY(ECT)", "teacher": "AKS", "room": "F-12", "hours": 3},
        {"code": "TH-MDM-DSP", "name": "MDM - DSP", "type": "Theory", "class": "TY(ECT)", "teacher": "DJT", "room": "F-12", "hours": 3},
        {"code": "PR-DSPL", "name": "DSP Lab", "type": "Practical", "class": "TY(ECT)", "teacher": "AKS", "room": "F-20", "hours": 8},
        {"code": "PR-ACL", "name": "Analog Communication Lab", "type": "Practical", "class": "TY(ECT)", "teacher": "VSJ", "room": "F-19", "hours": 8},

        # B.E. / Final Year - Sem 7
        {"code": "TH-HSSMC-EE&FM", "name": "Engineering Economics & Financial Mgmt", "type": "Theory", "class": "BY(ECT)", "teacher": "MVM", "room": "F-13", "hours": 4},
        {"code": "TH-PEC 4-GA(FOC)", "name": "Fiber Optic Communication / PEC 4", "type": "Theory", "class": "BY(ECT)", "teacher": "Dr.MRB", "room": "F-13", "hours": 4},
        {"code": "TH-OEC3-MC", "name": "Microcontrollers (OEC3)", "type": "Theory", "class": "BY(ECT)", "teacher": "SSA", "room": "F-13", "hours": 4},
        {"code": "TH-OEC 4-EWM", "name": "Electronic Waste Management (OEC 4)", "type": "Theory", "class": "BY(ECT)", "teacher": "VSJ", "room": "F-13", "hours": 4},
        {"code": "TH-ME-PPC 10", "name": "Professional Practice Course 10", "type": "Theory", "class": "BY(ECT)", "teacher": "PPK", "room": "F-13", "hours": 4},
        {"code": "PR-MProj3", "name": "Major Project-I / M.Proj3", "type": "Practical", "class": "BY(ECT)", "teacher": "Dr.KPP", "room": "F-20", "hours": 8},
        {"code": "PR-ME", "name": "Microwave Engineering Lab", "type": "Practical", "class": "BY(ECT)", "teacher": "PPK", "room": "F-14A", "hours": 8},
        {"code": "Mentor-Meeting", "name": "Mentor Mentee Meeting", "type": "Meeting", "class": "BY(ECT)", "teacher": "SSA", "room": "F-13", "hours": 2},

        # Other Cross-Department Subjects (FY-MGM, SY-A&R, BY-Mech)
        {"code": "TH-FY-PPS", "name": "Programming for Problem Solving", "type": "Theory", "class": "FY(MGM)", "teacher": "AKS", "room": "F-12", "hours": 4},
        {"code": "TH-AR-ADE", "name": "Analog & Digital Electronics", "type": "Theory", "class": "SY-A&R", "teacher": "KAP", "room": "F-13", "hours": 4},
        {"code": "TH-MECH-IPR", "name": "Intellectual Property Rights", "type": "Theory", "class": "BY-Mech", "teacher": "KAP", "room": "F-13", "hours": 4}
    ]

    subject_map = {}
    for sub in subjects_data:
        s = Subject.query.filter_by(code=sub["code"]).first()
        cls_obj = class_map.get(sub.get("class"))
        tch_obj = teacher_map.get(sub.get("teacher"))
        rm_obj = room_map.get(sub.get("room"))
        if not s:
            s = Subject(
                code=sub["code"],
                name=sub["name"],
                subject_type=sub["type"],
                class_id=cls_obj.id if cls_obj else None,
                default_teacher_id=tch_obj.id if tch_obj else None,
                default_room_id=rm_obj.id if rm_obj else None,
                weekly_hours=sub.get("hours", 4)
            )
            db.session.add(s)
            db.session.flush()
        subject_map[s.code] = s

    # 8. Seed Official Teacher Workload Assignments from the New PDF!
    seed_official_workload(class_map, teacher_map, subject_map)

    # 9. Seed Authentic Timetable Entries
    if TimetableEntry.query.count() == 0:
        load_pdf_timetable_entries(class_map, batch_map, teacher_map, room_map, slot_map, subject_map)

    db.session.commit()
    print("Database successfully seeded with complete authentic Workload and Timetable data!")


def seed_official_workload(class_map, teacher_map, subject_map):
    """Populates exact teacher workload assignments from the official MGM COE Workload document."""
    if TeacherWorkloadAssignment.query.count() > 0:
        return

    workload_records = [
        # 1. Dr. S. L. Kotgire (Vice Principal) -> Total: 3 hrs
        {"teacher": "DR.SLK", "class": "SY(ECT)", "subject": "TH-PCC-NT-203", "th": 3, "pr": 0, "notes": "Vice Principal Load"},

        # 2. Dr. Mrs. K. P. Paithane (HOD) -> Total: 14 hrs
        {"teacher": "Dr.KPP", "class": "SY(ECT)", "subject": "TH-VEC-CoI-231", "th": 2, "pr": 0, "notes": "CoI Theory"},
        {"teacher": "Dr.KPP", "class": "TY(ECT)", "subject": "TH-PPC-DSP", "th": 4, "pr": 0, "notes": "DSP Theory"},
        {"teacher": "Dr.KPP", "class": "BY(ECT)", "subject": "PR-MProj3", "th": 0, "pr": 8, "notes": "4*2=8 Mini-Proj Lab"},

        # 3. Dr. M. R. Banwaskar -> Total: 14 hrs
        {"teacher": "Dr.MRB", "class": "SY(ECT)", "subject": "TH-HSSM-ED-232", "th": 2, "pr": 0, "notes": "ED Theory"},
        {"teacher": "Dr.MRB", "class": "BY(ECT)", "subject": "TH-PEC 4-GA(FOC)", "th": 4, "pr": 0, "notes": "FoC(GA) Theory"},
        {"teacher": "Dr.MRB", "class": "SY(ECT)", "subject": "PR-MProj", "th": 0, "pr": 8, "notes": "4*2=8 Mini-Proj Lab"},

        # 4. Mr. V. S. Jadhav -> Total: 19 hrs
        {"teacher": "VSJ", "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "th": 4, "pr": 0, "notes": "EWM Theory"},
        {"teacher": "VSJ", "class": "SY(ECT)", "subject": "TH-OE-XYZ", "th": 3, "pr": 0, "notes": "OE-AE Theory"},
        {"teacher": "VSJ", "class": "SY(ECT)", "subject": "PR-MProj", "th": 0, "pr": 4, "notes": "4*1=4 Mini-Proj"},
        {"teacher": "VSJ", "class": "BY(ECT)", "subject": "PR-MProj3", "th": 0, "pr": 4, "notes": "4*1=4 Mini-Proj"},
        {"teacher": "VSJ", "class": "TY(ECT)", "subject": "PR-ACL", "th": 0, "pr": 4, "notes": "2*2=4 AC Lab"},

        # 5. Ms. P. P. Kanadkhedkar -> Total: 21 hrs
        {"teacher": "PPK", "class": "BY(ECT)", "subject": "PR-ME", "th": 4, "pr": 8, "notes": "ME Theory (4) + 2*4=8 Lab"},
        {"teacher": "PPK", "class": "TY(ECT)", "subject": "TH-PEC-FoC", "th": 3, "pr": 0, "notes": "FoC(Ele) Theory"},
        {"teacher": "PPK", "class": "SY(ECT)", "subject": "PR-MProj", "th": 0, "pr": 4, "notes": "4*1=4 Mini-Proj"},
        {"teacher": "PPK", "class": "TY(ECT)", "subject": "PR-DSPL", "th": 0, "pr": 2, "notes": "2*1=2 DSP Lab"},

        # 6. Mr. Sayed Shoaib Anwar (TT Incharge) -> Total: 20 hrs
        {"teacher": "SSA", "class": "BY(ECT)", "subject": "TH-OEC3-MC", "th": 4, "pr": 0, "notes": "MC(GB) Theory"},
        {"teacher": "SSA", "class": "TY(ECT)", "subject": "TH-PCC-AC", "th": 3, "pr": 0, "notes": "AC Theory"},
        {"teacher": "SSA", "class": "SY(ECT)", "subject": "TH-PCCL-SL-207", "th": 1, "pr": 8, "notes": "SL Theory (1) + 2*4=8 Lab"},
        {"teacher": "SSA", "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "th": 4, "pr": 0, "notes": "MDM-IoT Theory"},

        # 7. Ms. A. K. Salve -> Total: 21 hrs
        {"teacher": "AKS", "class": "FY(MGM)", "subject": "TH-FY-PPS", "th": 4, "pr": 8, "notes": "PPS Theory (4) + 2*4=8 Lab"},
        {"teacher": "AKS", "class": "TY(ECT)", "subject": "TH-OE-XYZ", "th": 3, "pr": 0, "notes": "OEB Theory"},
        {"teacher": "AKS", "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "th": 4, "pr": 0, "notes": "MDM-IoT Theory"},
        {"teacher": "AKS", "class": "TY(ECT)", "subject": "PR-DSPL", "th": 0, "pr": 2, "notes": "2*1=2 DSP Lab"},

        # 8. Ms. V. M. Maithali -> Total: 20 hrs
        {"teacher": "MVM", "class": "TY(ECT)", "subject": "TH-PCC-EWT", "th": 4, "pr": 0, "notes": "EWT Theory"},
        {"teacher": "MVM", "class": "SY(ECT)", "subject": "PR-NT", "th": 0, "pr": 8, "notes": "2*4=8 NT Lab"},
        {"teacher": "MVM", "class": "BY(ECT)", "subject": "TH-HSSMC-EE&FM", "th": 4, "pr": 0, "notes": "EE&FM Theory"},
        {"teacher": "MVM", "class": "TY(ECT)", "subject": "PR-DSPL", "th": 0, "pr": 4, "notes": "2*2=4 DSP Lab"},

        # 9. Mr. D. J. Tuptewar -> Total: 21 hrs
        {"teacher": "DJT", "class": "SY(ECT)", "subject": "TH-PCC-EDC-202", "th": 4, "pr": 8, "notes": "EDC Theory (4) + 2*4=8 Lab"},
        {"teacher": "DJT", "class": "TY(ECT)", "subject": "TH-MDM-DSP", "th": 3, "pr": 0, "notes": "DSP(MDM) Theory"},
        {"teacher": "DJT", "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "th": 4, "pr": 0, "notes": "MDM-IoT Theory"},
        {"teacher": "DJT", "class": "BY(ECT)", "subject": "PR-MProj3", "th": 0, "pr": 2, "notes": "2*1=2 Mini-Proj"},

        # 10. Ms. A. B. Dalvi -> Total: 21 hrs
        {"teacher": "ABD", "class": "FY(MGM)", "subject": "TH-FY-PPS", "th": 4, "pr": 8, "notes": "PPS Theory (4) + 2*4=8 Lab"},
        {"teacher": "ABD", "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "th": 4, "pr": 0, "notes": "MDM-IoT Theory"},
        {"teacher": "ABD", "class": "SY(ECT)", "subject": "TH-OEI-PDE-233", "th": 3, "pr": 0, "notes": "OE-PDE Theory"},
        {"teacher": "ABD", "class": "BY(ECT)", "subject": "PR-MProj3", "th": 0, "pr": 2, "notes": "2*1=2 Mini-Proj"},

        # 11. Ms. Kuchan A. P. -> Total: 22 hrs
        {"teacher": "KAP", "class": "SY-A&R", "subject": "TH-AR-ADE", "th": 4, "pr": 6, "notes": "A&DE Theory (4) + 2*3=6 Lab"},
        {"teacher": "KAP", "class": "BY-Mech", "subject": "TH-MECH-IPR", "th": 4, "pr": 0, "notes": "IPR Theory"},
        {"teacher": "KAP", "class": "TY(ECT)", "subject": "PR-ACL", "th": 0, "pr": 4, "notes": "2*2=4 AC Lab"},
        {"teacher": "KAP", "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "th": 4, "pr": 0, "notes": "MDM-IoT Theory"},

        # 12. Dr. S. S. Patil (Maths) -> Total: 16 hrs
        {"teacher": "SSP", "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "th": 4, "pr": 0, "notes": "Engineering Maths-III"}
    ]

    for rec in workload_records:
        t = teacher_map.get(rec["teacher"])
        c = class_map.get(rec["class"])
        s = subject_map.get(rec["subject"])
        if t and c and s:
            tot = rec["th"] + rec["pr"]
            assignment = TeacherWorkloadAssignment(
                teacher_id=t.id,
                class_id=c.id,
                subject_id=s.id,
                theory_hours=rec["th"],
                practical_hours=rec["pr"],
                total_hours=tot,
                notes=rec.get("notes")
            )
            db.session.add(assignment)


def load_pdf_timetable_entries(class_map, batch_map, teacher_map, room_map, slot_map, subject_map):
    """Populates authentic timetable matrix from the PDF document."""
    entries = [
        # MONDAY
        {"day": "Monday", "slot": 3, "class": "SY(ECT)", "subject": "TH-PCC-EDC-202", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-PCC-EDC-202-DJT (F-12)"},
        {"day": "Monday", "slot": 4, "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "teacher": "SSP", "room": "F-12", "type": "Theory", "title": "TH-BSC-EM-III-201-SSP (F-12)"},
        {"day": "Monday", "slot": 6, "class": "SY(ECT)", "subject": "TH-OEI-PDE-233", "teacher": "ABD", "room": "F-12", "type": "Theory", "title": "TH-OEI-PDE-233 ABD (F-12)"},
        {"day": "Monday", "slot": 7, "class": "SY(ECT)", "subject": "TH-HSSM-ED-232", "teacher": "Dr.MRB", "room": "F-12", "type": "Theory", "title": "TH-HSSM-ED-232-Dr.MRB (F-12)"},
        {"day": "Monday", "slot": 9, "class": "SY(ECT)", "batch": "S3", "subject": "PR-MProj", "teacher": "PPK", "room": "F-14B", "type": "Practical", "title": "PR-S3-MProj-14B(CP&CL)-PPK", "span": 2},
        {"day": "Monday", "slot": 9, "class": "SY(ECT)", "batch": "S4", "subject": "PR-NT", "teacher": "MVM", "room": "F-19", "type": "Practical", "title": "PR-S4-NT-F-19(CSL)-MVM", "span": 2},

        {"day": "Monday", "slot": 3, "class": "TY(ECT)", "batch": "T1", "subject": "PR-DSPL", "teacher": "AKS", "room": "F-20", "type": "Practical", "title": "PR-T1-DSPL-F-20 (ESDL)-AKS", "span": 2},
        {"day": "Monday", "slot": 3, "class": "TY(ECT)", "batch": "T2", "subject": "PR-ACL", "teacher": "VSJ", "room": "F-19", "type": "Practical", "title": "PR-T2-ACL-F-19(CSL)-VSJ", "span": 2},
        {"day": "Monday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PCC-EWT", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-PCC-EWT-MVM- (F-13)"},
        {"day": "Monday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PEC-FoC", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-PEC-FoC-PPK (F-13)"},
        {"day": "Monday", "slot": 9, "class": "TY(ECT)", "subject": "TH-PPC-DSP", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-PPC-DSP-Dr.KPP (F-12)", "span": 2},

        {"day": "Monday", "slot": 3, "class": "BY(ECT)", "subject": "TH-HSSMC-EE&FM", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-HSSMC-EE&FM-MVM (F-13)"},
        {"day": "Monday", "slot": 4, "class": "BY(ECT)", "subject": "TH-PEC 4-GA(FOC)", "teacher": "Dr.MRB", "room": "F-13", "type": "Theory", "title": "TH-PEC 4- GA(FOC)-Dr.MRB- (F-13)"},
        {"day": "Monday", "slot": 6, "class": "BY(ECT)", "batch": "B1", "subject": "PR-MProj3", "teacher": "Dr.KPP", "room": "F-20", "type": "Practical", "title": "PR-B1-MProj3-F-20(ESVL)-Dr.KPP", "span": 2},
        {"day": "Monday", "slot": 6, "class": "BY(ECT)", "batch": "B2", "subject": "PR-MProj3", "teacher": "Dr.KPP", "room": "F-19", "type": "Practical", "title": "PR-B2-M.Proj3-F-19(CSL)-Dr.KPP", "span": 2},
        {"day": "Monday", "slot": 6, "class": "BY(ECT)", "batch": "B3", "subject": "PR-MProj3", "teacher": "Dr.KPP", "room": "F-18", "type": "Practical", "title": "PR-B3-M.Proj3-F-18(EDCL)-Dr.KPP", "span": 2},
        {"day": "Monday", "slot": 6, "class": "BY(ECT)", "batch": "B4", "subject": "PR-MProj3", "teacher": "Dr.KPP", "room": "F-17", "type": "Practical", "title": "PR-B4-M.Proj3-F-17(DEML)-Dr.KPP", "span": 2},
        {"day": "Monday", "slot": 9, "class": "BY(ECT)", "subject": "TH-OEC3-MC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "TH-OEC3-MC-SSA- (F-13)"},
        {"day": "Monday", "slot": 10, "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "teacher": "VSJ", "room": "F-13", "type": "Theory", "title": "TH-OEC 4- EWM-VSJ- (F-13)"},

        # TUESDAY
        {"day": "Tuesday", "slot": 3, "class": "SY(ECT)", "subject": "TH-PCC-NT-203", "teacher": "DR.SLK", "room": "F-12", "type": "Theory", "title": "TH-PCC-NT-203-Dr.SLK (F-12)"},
        {"day": "Tuesday", "slot": 4, "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "teacher": "SSP", "room": "F-12", "type": "Theory", "title": "TH-BSC-EM-III-201-SSP (F-12)"},
        {"day": "Tuesday", "slot": 6, "class": "SY(ECT)", "subject": "TH-OEI-PDE-233", "teacher": "ABD", "room": "F-13", "type": "Theory", "title": "TH-OEI-PDE-233 ABD (F-13)"},
        {"day": "Tuesday", "slot": 7, "class": "SY(ECT)", "subject": "TH-PCC-EDC-202", "teacher": "DJT", "room": "F-13", "type": "Theory", "title": "TH-PCC-EDC-202-DJT (F-13)"},
        {"day": "Tuesday", "slot": 9, "class": "SY(ECT)", "batch": "S3", "subject": "PR-EDC", "teacher": "DJT", "room": "F-18", "type": "Practical", "title": "PR-S3-EDC-F-18(EDCL)-DJT", "span": 2},
        {"day": "Tuesday", "slot": 9, "class": "SY(ECT)", "batch": "S1", "subject": "PR-NT", "teacher": "MVM", "room": "F-19", "type": "Practical", "title": "PR-S1-NT-F-19(CSL)-MVM", "span": 2},

        {"day": "Tuesday", "slot": 4, "class": "TY(ECT)", "subject": "TH-PCC-EWT", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-PCC-EWT-MVM- (F-13)"},
        {"day": "Tuesday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PCC-AC", "teacher": "SSA", "room": "F-12", "type": "Theory", "title": "TH-PCC-AC-SSA- (F-12)"},
        {"day": "Tuesday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PPC-DSP", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-PPC-DSP-Dr.KPP (F-12)"},
        {"day": "Tuesday", "slot": 9, "class": "TY(ECT)", "batch": "T2", "subject": "PR-DSPL", "teacher": "PPK", "room": "F-20", "type": "Practical", "title": "PR-T2-DSPL-F-20 (ESVL)-PPK", "span": 2},
        {"day": "Tuesday", "slot": 9, "class": "TY(ECT)", "batch": "T1", "subject": "PR-ACL", "teacher": "VSJ", "room": "F-17", "type": "Practical", "title": "PR-T1-ACL-F-17(DEML)-VSJ", "span": 2},

        {"day": "Tuesday", "slot": 3, "class": "BY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-13", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},
        {"day": "Tuesday", "slot": 6, "class": "BY(ECT)", "batch": "B2", "subject": "PR-ME", "teacher": "PPK", "room": "F-14A", "type": "Practical", "title": "PR-B2-ME-F-14A(OC&ML)-PPK", "span": 2},
        {"day": "Tuesday", "slot": 6, "class": "BY(ECT)", "batch": "B3", "subject": "PR-MProj3", "teacher": "KAP", "room": "F-14", "type": "Practical", "title": "PR-B3-M.Proj3-F-14(CPSL)-KAP", "span": 2},
        {"day": "Tuesday", "slot": 9, "class": "BY(ECT)", "subject": "TH-OEC3-MC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "TH-OEC3-MC-SSA- (F-13)"},
        {"day": "Tuesday", "slot": 10, "class": "BY(ECT)", "subject": "TH-PEC 4-GA(FOC)", "teacher": "Dr.MRB", "room": "F-13", "type": "Theory", "title": "TH-PEC 4- GA(FOC)-Dr.MRB- (F-13)"},

        # WEDNESDAY
        {"day": "Wednesday", "slot": 1, "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "teacher": "SSA", "room": "F-13", "type": "Online", "title": "TH-MDM--IoT-Online SSA/AKS/DJT/ABD-(F-13)"},
        {"day": "Wednesday", "slot": 3, "class": "SY(ECT)", "subject": "TH-PCC-NT-203", "teacher": "DR.SLK", "room": "F-12", "type": "Theory", "title": "TH-PCC-NT-203-Dr.SLK (F-12)"},
        {"day": "Wednesday", "slot": 4, "class": "SY(ECT)", "subject": "TH-VEC-CoI-231", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-VEC-CoI-231-Dr.KPP (F-12)"},
        {"day": "Wednesday", "slot": 6, "class": "SY(ECT)", "subject": "TH-OEI-PDE-233", "teacher": "ABD", "room": "F-12", "type": "Theory", "title": "TH-OEI-PDE-233 ABD (F-12)"},
        {"day": "Wednesday", "slot": 7, "class": "SY(ECT)", "subject": "TH-PCC-EDC-202", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-PCC-EDC-202-DJT (F-12)"},
        {"day": "Wednesday", "slot": 9, "class": "SY(ECT)", "batch": "S2", "subject": "PR-NT", "teacher": "MVM", "room": "F-19", "type": "Practical", "title": "PR-S2-NT-F-19(CSL)-MVM", "span": 2},
        {"day": "Wednesday", "slot": 9, "class": "SY(ECT)", "batch": "S4", "subject": "PR-EDC", "teacher": "DJT", "room": "F-18", "type": "Practical", "title": "PR-S4-EDC-F-18(EDCL)-DJT", "span": 2},
        {"day": "Wednesday", "slot": 9, "class": "SY(ECT)", "batch": "S1", "subject": "PR-SL", "teacher": "SSA", "room": "F-20", "type": "Practical", "title": "PR-S1-SL-F-20(ESVL)-SSA", "span": 2},
        {"day": "Wednesday", "slot": 9, "class": "SY(ECT)", "batch": "S2", "subject": "PR-MProj", "teacher": "Dr.MRB", "room": "Lab 14A", "type": "Practical", "title": "PR-S2-MProj-14A(PCB&SL)-Dr.MRB", "span": 2},

        {"day": "Wednesday", "slot": 3, "class": "TY(ECT)", "batch": "T3", "subject": "PR-DSPL", "teacher": "MVM", "room": "F-14", "type": "Practical", "title": "PR-T3-DSPL-F-14 (CPSL)-MVM", "span": 2},
        {"day": "Wednesday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PCC-AC", "teacher": "SSA", "room": "F-12", "type": "Theory", "title": "TH-PCC-AC-SSA (F-12)"},
        {"day": "Wednesday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PPC-DSP", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-PPC-DSP-Dr.KPP (F-12)"},
        {"day": "Wednesday", "slot": 9, "class": "TY(ECT)", "subject": "TH-OE-XYZ", "teacher": "AKS", "room": "F-12", "type": "Theory", "title": "OE- TH-XYZ-AKS-(F-12)", "span": 2},

        {"day": "Wednesday", "slot": 3, "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "teacher": "VSJ", "room": "F-13", "type": "Theory", "title": "TH-OEC 4- EWM-VSJ- (F-13)"},
        {"day": "Wednesday", "slot": 4, "class": "BY(ECT)", "subject": "TH-ME-PPC 10", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-ME-PPC 10- PPK (F-13)"},
        {"day": "Wednesday", "slot": 6, "class": "BY(ECT)", "batch": "B3", "subject": "PR-ME", "teacher": "PPK", "room": "F-14A", "type": "Practical", "title": "PR-B3-ME-F-14A(OC&ML)-PPK", "span": 2},
        {"day": "Wednesday", "slot": 9, "class": "BY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-13", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},

        # THURSDAY
        {"day": "Thursday", "slot": 1, "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "teacher": "SSA", "room": "F-13", "type": "Online", "title": "TH-MDM--IoT-Online SSA/AKS/DJT/ABD-(F-13)"},
        {"day": "Thursday", "slot": 3, "class": "SY(ECT)", "subject": "TH-PCC-NT-203", "teacher": "DR.SLK", "room": "F-12", "type": "Theory", "title": "TH-PCC-NT-203-Dr.SLK (F-12)"},
        {"day": "Thursday", "slot": 4, "class": "SY(ECT)", "subject": "TH-VEC-CoI-231", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-VEC-CoI-231-Dr.KPP (F-12)"},
        {"day": "Thursday", "slot": 6, "class": "SY(ECT)", "batch": "S1", "subject": "PR-EDC", "teacher": "DJT", "room": "F-18", "type": "Practical", "title": "PR-S1-EDC-F-18(EDCL)-DJT", "span": 2},
        {"day": "Thursday", "slot": 6, "class": "SY(ECT)", "batch": "S2", "subject": "PR-SL", "teacher": "SSA", "room": "F-20", "type": "Practical", "title": "PR-S2-SL-F-20(ESVL)-SSA", "span": 2},
        {"day": "Thursday", "slot": 6, "class": "SY(ECT)", "batch": "S3", "subject": "PR-MProj", "teacher": "Dr.MRB", "room": "Lab 14", "type": "Practical", "title": "PR-S3-MProj-14(PCBL)-Dr.MRB", "span": 2},
        {"day": "Thursday", "slot": 9, "class": "SY(ECT)", "batch": "S1", "subject": "PR-MProj", "teacher": "VSJ", "room": "Lab 14", "type": "Practical", "title": "PR-S1-MProj-14(PCBL)-VSJ", "span": 2},
        {"day": "Thursday", "slot": 9, "class": "SY(ECT)", "batch": "S2", "subject": "PR-NT", "teacher": "MVM", "room": "F-18", "type": "Practical", "title": "PR-S2-NT-F-18(EDCL)-MVM", "span": 2},
        {"day": "Thursday", "slot": 9, "class": "SY(ECT)", "batch": "S3", "subject": "PR-SL", "teacher": "SSA", "room": "F-20", "type": "Practical", "title": "PR-S3-SL-F-20(ESDL)-SSA", "span": 2},

        {"day": "Thursday", "slot": 1, "class": "TY(ECT)", "subject": "TH-MDM-DSP", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-MDM--DSP-DJT- (F-12)"},
        {"day": "Thursday", "slot": 3, "class": "TY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-12", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},
        {"day": "Thursday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PEC-FoC", "teacher": "PPK", "room": "F-12", "type": "Theory", "title": "TH-PEC-FoC-PPK (F-12)"},
        {"day": "Thursday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PPC-DSP", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-PPC-DSP-Dr.KPP (F-12)"},
        {"day": "Thursday", "slot": 9, "class": "TY(ECT)", "batch": "T4", "subject": "PR-ACL", "teacher": "KAP", "room": "F-19", "type": "Practical", "title": "PR-T4-ACL-F-19(CSL)-KAP", "span": 2},

        {"day": "Thursday", "slot": 3, "class": "BY(ECT)", "subject": "TH-ME-PPC 10", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-ME-PPC 10- PPK (F-13)"},
        {"day": "Thursday", "slot": 4, "class": "BY(ECT)", "subject": "TH-OEC3-MC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "TH-OEC3-MC-SSA- (F-13)"},
        {"day": "Thursday", "slot": 6, "class": "BY(ECT)", "subject": "TH-HSSMC-EE&FM", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-HSSMC-EE&FM-MVM (F-13)"},
        {"day": "Thursday", "slot": 7, "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "teacher": "VSJ", "room": "F-13", "type": "Theory", "title": "TH-OEC 4- EWM-VSJ- (F-13)"},
        {"day": "Thursday", "slot": 9, "class": "BY(ECT)", "batch": "B4", "subject": "PR-ME", "teacher": "PPK", "room": "F-14A", "type": "Practical", "title": "PR-B4-ME-F-14A(OC&ML)-PPK", "span": 2},

        # FRIDAY
        {"day": "Friday", "slot": 1, "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "teacher": "SSA", "room": "F-13", "type": "Online", "title": "TH-MDM--IoT-Online SSA/AKS/DJT/ABD-(F-13)"},
        {"day": "Friday", "slot": 3, "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "teacher": "SSP", "room": "F-12", "type": "Theory", "title": "TH-BSC-EM-III-201-SSP (F-12)"},
        {"day": "Friday", "slot": 4, "class": "SY(ECT)", "subject": "TH-HSSM-ED-232", "teacher": "Dr.MRB", "room": "F-12", "type": "Theory", "title": "TH-HSSM-ED-232-Dr.MRB (F-12)"},
        {"day": "Friday", "slot": 6, "class": "SY(ECT)", "batch": "S2", "subject": "PR-EDC", "teacher": "DJT", "room": "F-18", "type": "Practical", "title": "PR-S2-EDC-F-18(EDCL)-DJT", "span": 2},
        {"day": "Friday", "slot": 6, "class": "SY(ECT)", "batch": "S4", "subject": "PR-MProj", "teacher": "Dr.MRB", "room": "Lab 14", "type": "Practical", "title": "PR-S4-MProj-14(PCBL)-Dr.MRB", "span": 2},
        {"day": "Friday", "slot": 9, "class": "SY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-12", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},

        {"day": "Friday", "slot": 1, "class": "TY(ECT)", "subject": "TH-MDM-DSP", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-MDM--DSP-DJT- (F-12)"},
        {"day": "Friday", "slot": 3, "class": "TY(ECT)", "subject": "TH-OE-XYZ", "teacher": "AKS", "room": "F-13", "type": "Theory", "title": "TH-OE-XYZ-AKS- (F-13)"},
        {"day": "Friday", "slot": 4, "class": "TY(ECT)", "subject": "TH-PCC-EWT", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-PCC-EWT-MVM- (F-13)"},
        {"day": "Friday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PEC-FoC", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-PEC-FoC-PPK (F-13)"},
        {"day": "Friday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PCC-AC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "PCC- TH-AC-SSA (F-13)"},
        {"day": "Friday", "slot": 9, "class": "TY(ECT)", "batch": "T3", "subject": "PR-ACL", "teacher": "KAP", "room": "F-19", "type": "Practical", "title": "PR-T3-ACL-F-19(CSL)-KAP", "span": 2},

        {"day": "Friday", "slot": 3, "class": "BY(ECT)", "batch": "B1", "subject": "PR-ME", "teacher": "PPK", "room": "F-14A", "type": "Practical", "title": "PR-B1-ME-F-14A(OC&ML)-PPK", "span": 2},
        {"day": "Friday", "slot": 3, "class": "BY(ECT)", "batch": "B2", "subject": "PR-MProj3", "teacher": "DJT", "room": "F-17", "type": "Practical", "title": "PR-B2-M.Proj3-F-17(DEML)-DJT", "span": 2},
        {"day": "Friday", "slot": 3, "class": "BY(ECT)", "batch": "B4", "subject": "PR-MProj3", "teacher": "VSJ", "room": "Lab 14A", "type": "Practical", "title": "PR-B4-M.Proj3-14A(PCB&SL)-VSJ", "span": 2},
        {"day": "Friday", "slot": 6, "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "teacher": "VSJ", "room": "F-13", "type": "Theory", "title": "TH-OEC 4- EWM-VSJ- (F-13)"},
        {"day": "Friday", "slot": 7, "class": "BY(ECT)", "subject": "TH-HSSMC-EE&FM", "teacher": "MVM", "room": "F-12", "type": "Theory", "title": "TH-HSSMC-EE&FM-MVM (F-12)"},
        {"day": "Friday", "slot": 9, "class": "BY(ECT)", "subject": "TH-PEC 4-GA(FOC)", "teacher": "Dr.MRB", "room": "F-13", "type": "Theory", "title": "TH-PEC 4- GA(FOC)-Dr.MRB- (F-13)"},
        {"day": "Friday", "slot": 10, "class": "BY(ECT)", "subject": "TH-ME-PPC 10", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-ME-PPC 10- PPK (F-13)"},

        # SATURDAY
        {"day": "Saturday", "slot": 1, "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "teacher": "SSA", "room": "F-13", "type": "Practical", "title": "PR-MDM--IoT-Online SSA/AKS/DJT/ABD-(F-13)"},
        {"day": "Saturday", "slot": 3, "class": "SY(ECT)", "batch": "S2", "subject": "PR-MProj", "teacher": "PPK", "room": "F-19", "type": "Practical", "title": "PR-S2-MProj-F-19(CSL)-PPK", "span": 2},
        {"day": "Saturday", "slot": 3, "class": "SY(ECT)", "batch": "S4", "subject": "PR-SL", "teacher": "SSA", "room": "F-20", "type": "Practical", "title": "PR-S4-SL-F-20(ESVL)-SSA", "span": 2},
        {"day": "Saturday", "slot": 6, "class": "SY(ECT)", "subject": "TH-PCCL-SL-207", "teacher": "SSA", "room": "F-12", "type": "Theory", "title": "TH-PCCL-SL-207-SSA (F-12)"},
        {"day": "Saturday", "slot": 7, "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "teacher": "SSP", "room": "F-12", "type": "Theory", "title": "TH-BSC-EM-III-201-SSP (F-12)"},
        {"day": "Saturday", "slot": 9, "class": "SY(ECT)", "batch": "S4", "subject": "PR-MProj", "teacher": "VSJ", "room": "F-19", "type": "Practical", "title": "PR-S4-MProj-F19(CSL)-VSJ", "span": 2},
        {"day": "Saturday", "slot": 9, "class": "SY(ECT)", "batch": "S1", "subject": "PR-MProj", "teacher": "Dr.MRB", "room": "Lab 14A", "type": "Practical", "title": "PR-S1-MProj-14A(PCB&SL)-Dr.MRB", "span": 2},

        {"day": "Saturday", "slot": 1, "class": "TY(ECT)", "subject": "TH-MDM-DSP", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-MDM--DSP-DJT- (F-12)"},
        {"day": "Saturday", "slot": 3, "class": "TY(ECT)", "subject": "TH-OE-XYZ", "teacher": "AKS", "room": "F-13", "type": "Theory", "title": "TH-OE-XYZ-AKS- (F-13)"},
        {"day": "Saturday", "slot": 4, "class": "TY(ECT)", "subject": "TH-PCC-EWT", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-PCC-EWT-MVM- (F-13)"},
        {"day": "Saturday", "slot": 6, "class": "TY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-13", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},
        {"day": "Saturday", "slot": 9, "class": "TY(ECT)", "batch": "T4", "subject": "PR-DSPL", "teacher": "MVM", "room": "F-14B", "type": "Practical", "title": "PR-T4-DSPL-F-14B (CP&CL)-MVM", "span": 2},

        {"day": "Saturday", "slot": 3, "class": "BY(ECT)", "batch": "B1", "subject": "PR-MProj3", "teacher": "VSJ", "room": "F-14B", "type": "Practical", "title": "PR-B1-M.Proj3-14B(CP&CL)-VSJ", "span": 2},
        {"day": "Saturday", "slot": 6, "class": "BY(ECT)", "subject": "TH-PEC 4-GA(FOC)", "teacher": "Dr.MRB", "room": "F-13", "type": "Theory", "title": "TH-PEC 4- GA(FOC)-Dr.MRB (F-13)"},
        {"day": "Saturday", "slot": 7, "class": "BY(ECT)", "subject": "TH-ME-PPC 10", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-ME-PPC 10- PPK (F-13)"},
        {"day": "Saturday", "slot": 9, "class": "BY(ECT)", "subject": "TH-HSSMC-EE&FM", "teacher": "MVM", "room": "F-12", "type": "Theory", "title": "TH-HSSMC-EE&FM-MVM (F-12)"},
        {"day": "Saturday", "slot": 10, "class": "BY(ECT)", "subject": "TH-OEC3-MC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "TH-OEC3-MC-SSA-(F-13)"}
    ]

    for item in entries:
        cls_obj = class_map[item["class"]]
        batch_obj = batch_map.get(item.get("batch"))
        teacher_obj = teacher_map.get(item.get("teacher"))
        room_obj = room_map.get(item.get("room"))
        slot_obj = slot_map[item["slot"]]
        sub_obj = subject_map.get(item.get("subject"))

        entry = TimetableEntry(
            day=item["day"],
            slot_id=slot_obj.id,
            class_id=cls_obj.id,
            batch_id=batch_obj.id if batch_obj else None,
            subject_id=sub_obj.id if sub_obj else None,
            teacher_id=teacher_obj.id if teacher_obj else None,
            room_id=room_obj.id if room_obj else None,
            entry_type=item.get("type", "Theory"),
            custom_title=item.get("title"),
            custom_teacher=teacher_obj.code if teacher_obj else None,
            custom_room=room_obj.name if room_obj else None,
            custom_batch=batch_obj.name if batch_obj else ("All" if item.get("type") == "Theory" else None),
            span_slots=item.get("span", 1)
        )
        db.session.add(entry)
