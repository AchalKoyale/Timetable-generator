import os
from models import db, User, Teacher, Room, AcademicClass, Batch, Subject, TimeSlot, TimetableEntry, CollegeSetting

def seed_database():
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
        {"name": "Dr. Mr. S. L. KOTGIRE", "code": "DR.SLK", "designation": "Associate Professor", "email": "slkotgire@mgmcen.ac.in"},
        {"name": "Dr. Mrs. K. P. PAITHANE", "code": "Dr.KPP", "designation": "Professor & Head", "email": "kppaithane@mgmcen.ac.in"},
        {"name": "Dr. M. R. BANWASKAR", "code": "Dr.MRB", "designation": "Assistant Professor", "email": "mrbanwaskar@mgmcen.ac.in"},
        {"name": "Mr. V. S. JADHAV", "code": "VSJ", "designation": "Assistant Professor", "email": "vsjadhav@mgmcen.ac.in"},
        {"name": "Ms. P. P. KANADKHEDKAR", "code": "PPK", "designation": "Assistant Professor", "email": "ppkanadkhedkar@mgmcen.ac.in"},
        {"name": "Mr. SAYED SHOAIB ANWAR", "code": "SSA", "designation": "Assistant Professor / TT Incharge", "email": "ssanwar@mgmcen.ac.in"},
        {"name": "Ms. A. K. SALVE", "code": "AKS", "designation": "Assistant Professor / Dept Coordinator", "email": "aksalve@mgmcen.ac.in"},
        {"name": "Ms. MAITHILI V. M.", "code": "MVM", "designation": "Assistant Professor", "email": "mvmaithili@mgmcen.ac.in"},
        {"name": "Mr. D. J. TUPTEWAR", "code": "DJT", "designation": "Assistant Professor", "email": "djtuptewar@mgmcen.ac.in"},
        {"name": "Ms. A. B. DALVI", "code": "ABD", "designation": "Assistant Professor", "email": "abdalvi@mgmcen.ac.in"},
        {"name": "Ms. KUCHAN A. P.", "code": "KAP", "designation": "Assistant Professor", "email": "apkuchan@mgmcen.ac.in"},
        {"name": "Dr. S. S. PATIL", "code": "SSP", "designation": "Assistant Professor (Maths)", "email": "sspatil@mgmcen.ac.in"}
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
                max_weekly_hours=22
            )
            db.session.add(t)
            db.session.flush()
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

    # 5. Classes and Batches (SY, TY, BY)
    classes_data = [
        {"name": "SY(ECT)", "year_name": "Second Year", "semester": 3, "batches": [("S1", "1-20"), ("S2", "21-40"), ("S3", "41-60"), ("S4", "61 Onwards")]},
        {"name": "TY(ECT)", "year_name": "Third Year", "semester": 5, "batches": [("T1", "1-20"), ("T2", "21-40"), ("T3", "41-60"), ("T4", "61 Onwards")]},
        {"name": "BY(ECT)", "year_name": "Final Year / B.E.", "semester": 7, "batches": [("B1", "1-20"), ("B2", "21-40"), ("B3", "41-60"), ("B4", "61 Onwards")]}
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
    # 08:00 TO 09:00 Or 10:00 | 10:00 TO 10:30 Recess | 10:30 TO 11:30 | 11:30 TO 12:30 | 12:30 TO 01:00 Recess | 01:00 TO 02:00 | 02:00 TO 03:00 | 03:00 TO 03:30 Recess | 03:30 To 04:30 | 04:30 TO 05:30
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
        {"code": "TH-BSC-EM-III-201", "name": "Engineering Mathematics-III", "type": "Theory", "class": "SY(ECT)", "teacher": "SSP", "room": "F-12"},
        {"code": "TH-PCC-EDC-202", "name": "Electronic Devices & Circuits", "type": "Theory", "class": "SY(ECT)", "teacher": "DJT", "room": "F-12"},
        {"code": "TH-PCC-NT-203", "name": "Network Theory", "type": "Theory", "class": "SY(ECT)", "teacher": "DR.SLK", "room": "F-12"},
        {"code": "TH-OEI-PDE-233", "name": "Partial Differential Equations", "type": "Theory", "class": "SY(ECT)", "teacher": "ABD", "room": "F-12"},
        {"code": "TH-HSSM-ED-232", "name": "Entrepreneurship Development", "type": "Theory", "class": "SY(ECT)", "teacher": "Dr.MRB", "room": "F-12"},
        {"code": "TH-VEC-CoI-231", "name": "Constitution of India", "type": "Theory", "class": "SY(ECT)", "teacher": "Dr.KPP", "room": "F-12"},
        {"code": "TH-PCCL-SL-207", "name": "Skill Lab Theory", "type": "Theory", "class": "SY(ECT)", "teacher": "SSA", "room": "F-12"},
        {"code": "TH-MDM-IoT-Online", "name": "Multidisciplinary Minor - IoT", "type": "Online", "class": "SY(ECT)", "teacher": "SSA", "room": "F-13"},
        {"code": "PR-EDC", "name": "Electronic Devices & Circuits Lab", "type": "Practical", "class": "SY(ECT)", "teacher": "DJT", "room": "F-18"},
        {"code": "PR-NT", "name": "Network Theory Lab", "type": "Practical", "class": "SY(ECT)", "teacher": "MVM", "room": "F-19"},
        {"code": "PR-SL", "name": "Skill Lab Practical", "type": "Practical", "class": "SY(ECT)", "teacher": "SSA", "room": "F-20"},
        {"code": "PR-MProj", "name": "Mini Project Lab", "type": "Practical", "class": "SY(ECT)", "teacher": "PPK", "room": "F-14B"},

        # T.Y. (ECT) - Sem 5
        {"code": "TH-PCC-EWT", "name": "Electromagnetic Waves & Transmission", "type": "Theory", "class": "TY(ECT)", "teacher": "MVM", "room": "F-13"},
        {"code": "TH-PEC-FoC", "name": "Fundamentals of Communication", "type": "Theory", "class": "TY(ECT)", "teacher": "PPK", "room": "F-13"},
        {"code": "TH-PPC-DSP", "name": "Digital Signal Processing", "type": "Theory", "class": "TY(ECT)", "teacher": "Dr.KPP", "room": "F-12"},
        {"code": "TH-PCC-AC", "name": "Analog Communication", "type": "Theory", "class": "TY(ECT)", "teacher": "SSA", "room": "F-12"},
        {"code": "TH-OE-XYZ", "name": "Open Elective (OE-XYZ)", "type": "Theory", "class": "TY(ECT)", "teacher": "AKS", "room": "F-12"},
        {"code": "TH-MDM-DSP", "name": "MDM - DSP", "type": "Theory", "class": "TY(ECT)", "teacher": "DJT", "room": "F-12"},
        {"code": "PR-DSPL", "name": "DSP Lab", "type": "Practical", "class": "TY(ECT)", "teacher": "AKS", "room": "F-20"},
        {"code": "PR-ACL", "name": "Analog Communication Lab", "type": "Practical", "class": "TY(ECT)", "teacher": "VSJ", "room": "F-19"},

        # B.E. / Final Year - Sem 7
        {"code": "TH-HSSMC-EE&FM", "name": "Engineering Economics & Financial Mgmt", "type": "Theory", "class": "BY(ECT)", "teacher": "MVM", "room": "F-13"},
        {"code": "TH-PEC 4-GA(FOC)", "name": "Fiber Optic Communication / PEC 4", "type": "Theory", "class": "BY(ECT)", "teacher": "Dr.MRB", "room": "F-13"},
        {"code": "TH-OEC3-MC", "name": "Microcontrollers (OEC3)", "type": "Theory", "class": "BY(ECT)", "teacher": "SSA", "room": "F-13"},
        {"code": "TH-OEC 4-EWM", "name": "Electronic Waste Management (OEC 4)", "type": "Theory", "class": "BY(ECT)", "teacher": "VSJ", "room": "F-13"},
        {"code": "TH-ME-PPC 10", "name": "Professional Practice Course 10", "type": "Theory", "class": "BY(ECT)", "teacher": "PPK", "room": "F-13"},
        {"code": "PR-MProj3", "name": "Major Project-I / M.Proj3", "type": "Practical", "class": "BY(ECT)", "teacher": "Dr.KPP", "room": "F-20"},
        {"code": "PR-ME", "name": "Microwave Engineering Lab", "type": "Practical", "class": "BY(ECT)", "teacher": "PPK", "room": "F-14A"},
        {"code": "Mentor-Meeting", "name": "Mentor Mentee Meeting", "type": "Meeting", "class": "BY(ECT)", "teacher": "SSA", "room": "F-13"}
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
                default_room_id=rm_obj.id if rm_obj else None
            )
            db.session.add(s)
            db.session.flush()
        subject_map[s.code] = s

    # 8. Insert Complete Authentic Timetable Entries from PDF!
    # If entries already exist, we keep them or reset them
    if TimetableEntry.query.count() == 0:
        load_pdf_timetable_entries(class_map, batch_map, teacher_map, room_map, slot_map, subject_map)

    db.session.commit()
    print("Database successfully seeded with PDF data!")


def load_pdf_timetable_entries(class_map, batch_map, teacher_map, room_map, slot_map, subject_map):
    """
    Populates the EXACT timetable matrix from the PDF document.
    Slot Mapping:
    slot 1: 08:00 - 10:00 (MDM online)
    slot 2: 10:00 - 10:30 (Recess)
    slot 3: 10:30 - 11:30
    slot 4: 11:30 - 12:30
    slot 5: 12:30 - 01:00 (Lunch Recess)
    slot 6: 01:00 - 02:00
    slot 7: 02:00 - 03:00
    slot 8: 03:00 - 03:30 (Recess)
    slot 9: 03:30 - 04:30
    slot 10: 04:30 - 05:30
    """

    entries = [
        # ========================================================
        # MONDAY
        # ========================================================
        # SY(ECT)
        {"day": "Monday", "slot": 3, "class": "SY(ECT)", "subject": "TH-PCC-EDC-202", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-PCC-EDC-202-DJT (F-12)"},
        {"day": "Monday", "slot": 4, "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "teacher": "SSP", "room": "F-12", "type": "Theory", "title": "TH-BSC-EM-III-201-SSP (F-12)"},
        {"day": "Monday", "slot": 6, "class": "SY(ECT)", "subject": "TH-OEI-PDE-233", "teacher": "ABD", "room": "F-12", "type": "Theory", "title": "TH-OEI-PDE-233 ABD (F-12)"},
        {"day": "Monday", "slot": 7, "class": "SY(ECT)", "subject": "TH-HSSM-ED-232", "teacher": "Dr.MRB", "room": "F-12", "type": "Theory", "title": "TH-HSSM-ED-232-Dr.MRB (F-12)"},
        {"day": "Monday", "slot": 9, "class": "SY(ECT)", "batch": "S3", "subject": "PR-MProj", "teacher": "PPK", "room": "F-14B", "type": "Practical", "title": "PR-S3-MProj-14B(CP&CL)-PPK", "span": 2},
        {"day": "Monday", "slot": 9, "class": "SY(ECT)", "batch": "S4", "subject": "PR-NT", "teacher": "MVM", "room": "F-19", "type": "Practical", "title": "PR-S4-NT-F-19(CSL)-MVM", "span": 2},

        # TY(ECT)
        {"day": "Monday", "slot": 3, "class": "TY(ECT)", "batch": "T1", "subject": "PR-DSPL", "teacher": "AKS", "room": "F-20", "type": "Practical", "title": "PR-T1-DSPL-F-20 (ESDL)-AKS", "span": 2},
        {"day": "Monday", "slot": 3, "class": "TY(ECT)", "batch": "T2", "subject": "PR-ACL", "teacher": "VSJ", "room": "F-19", "type": "Practical", "title": "PR-T2-ACL-F-19(CSL)-VSJ", "span": 2},
        {"day": "Monday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PCC-EWT", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-PCC-EWT-MVM- (F-13)"},
        {"day": "Monday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PEC-FoC", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-PEC-FoC-PPK (F-13)"},
        {"day": "Monday", "slot": 9, "class": "TY(ECT)", "subject": "TH-PPC-DSP", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-PPC-DSP-Dr.KPP (F-12)", "span": 2},

        # BY(ECT)
        {"day": "Monday", "slot": 3, "class": "BY(ECT)", "subject": "TH-HSSMC-EE&FM", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-HSSMC-EE&FM-MVM (F-13)"},
        {"day": "Monday", "slot": 4, "class": "BY(ECT)", "subject": "TH-PEC 4-GA(FOC)", "teacher": "Dr.MRB", "room": "F-13", "type": "Theory", "title": "TH-PEC 4- GA(FOC)-Dr.MRB- (F-13)"},
        {"day": "Monday", "slot": 6, "class": "BY(ECT)", "batch": "B1", "subject": "PR-MProj3", "teacher": "Dr.KPP", "room": "F-20", "type": "Practical", "title": "PR-B1-MProj3-F-20(ESVL)-Dr.KPP", "span": 2},
        {"day": "Monday", "slot": 6, "class": "BY(ECT)", "batch": "B2", "subject": "PR-MProj3", "teacher": "Dr.KPP", "room": "F-19", "type": "Practical", "title": "PR-B2-M.Proj3-F-19(CSL)-Dr.KPP", "span": 2},
        {"day": "Monday", "slot": 6, "class": "BY(ECT)", "batch": "B3", "subject": "PR-MProj3", "teacher": "Dr.KPP", "room": "F-18", "type": "Practical", "title": "PR-B3-M.Proj3-F-18(EDCL)-Dr.KPP", "span": 2},
        {"day": "Monday", "slot": 6, "class": "BY(ECT)", "batch": "B4", "subject": "PR-MProj3", "teacher": "Dr.KPP", "room": "F-17", "type": "Practical", "title": "PR-B4-M.Proj3-F-17(DEML)-Dr.KPP", "span": 2},
        {"day": "Monday", "slot": 9, "class": "BY(ECT)", "subject": "TH-OEC3-MC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "TH-OEC3-MC-SSA- (F-13)"},
        {"day": "Monday", "slot": 10, "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "teacher": "VSJ", "room": "F-13", "type": "Theory", "title": "TH-OEC 4- EWM-VSJ- (F-13)"},

        # ========================================================
        # TUESDAY
        # ========================================================
        # SY(ECT)
        {"day": "Tuesday", "slot": 3, "class": "SY(ECT)", "subject": "TH-PCC-NT-203", "teacher": "DR.SLK", "room": "F-12", "type": "Theory", "title": "TH-PCC-NT-203-Dr.SLK (F-12)"},
        {"day": "Tuesday", "slot": 4, "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "teacher": "SSP", "room": "F-12", "type": "Theory", "title": "TH-BSC-EM-III-201-SSP (F-12)"},
        {"day": "Tuesday", "slot": 6, "class": "SY(ECT)", "subject": "TH-OEI-PDE-233", "teacher": "ABD", "room": "F-13", "type": "Theory", "title": "TH-OEI-PDE-233 ABD (F-13)"},
        {"day": "Tuesday", "slot": 7, "class": "SY(ECT)", "subject": "TH-PCC-EDC-202", "teacher": "DJT", "room": "F-13", "type": "Theory", "title": "TH-PCC-EDC-202-DJT (F-13)"},
        {"day": "Tuesday", "slot": 9, "class": "SY(ECT)", "batch": "S3", "subject": "PR-EDC", "teacher": "DJT", "room": "F-18", "type": "Practical", "title": "PR-S3-EDC-F-18(EDCL)-DJT", "span": 2},
        {"day": "Tuesday", "slot": 9, "class": "SY(ECT)", "batch": "S1", "subject": "PR-NT", "teacher": "MVM", "room": "F-19", "type": "Practical", "title": "PR-S1-NT-F-19(CSL)-MVM", "span": 2},

        # TY(ECT)
        {"day": "Tuesday", "slot": 4, "class": "TY(ECT)", "subject": "TH-PCC-EWT", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-PCC-EWT-MVM- (F-13)"},
        {"day": "Tuesday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PCC-AC", "teacher": "SSA", "room": "F-12", "type": "Theory", "title": "TH-PCC-AC-SSA- (F-12)"},
        {"day": "Tuesday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PPC-DSP", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-PPC-DSP-Dr.KPP (F-12)"},
        {"day": "Tuesday", "slot": 9, "class": "TY(ECT)", "batch": "T2", "subject": "PR-DSPL", "teacher": "PPK", "room": "F-20", "type": "Practical", "title": "PR-T2-DSPL-F-20 (ESVL)-PPK", "span": 2},
        {"day": "Tuesday", "slot": 9, "class": "TY(ECT)", "batch": "T1", "subject": "PR-ACL", "teacher": "VSJ", "room": "F-17", "type": "Practical", "title": "PR-T1-ACL-F-17(DEML)-VSJ", "span": 2},

        # BY(ECT)
        {"day": "Tuesday", "slot": 3, "class": "BY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-13", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},
        {"day": "Tuesday", "slot": 6, "class": "BY(ECT)", "batch": "B2", "subject": "PR-ME", "teacher": "PPK", "room": "F-14A", "type": "Practical", "title": "PR-B2-ME-F-14A(OC&ML)-PPK", "span": 2},
        {"day": "Tuesday", "slot": 6, "class": "BY(ECT)", "batch": "B3", "subject": "PR-MProj3", "teacher": "KAP", "room": "F-14", "type": "Practical", "title": "PR-B3-M.Proj3-F-14(CPSL)-KAP", "span": 2},
        {"day": "Tuesday", "slot": 9, "class": "BY(ECT)", "subject": "TH-OEC3-MC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "TH-OEC3-MC-SSA- (F-13)"},
        {"day": "Tuesday", "slot": 10, "class": "BY(ECT)", "subject": "TH-PEC 4-GA(FOC)", "teacher": "Dr.MRB", "room": "F-13", "type": "Theory", "title": "TH-PEC 4- GA(FOC)-Dr.MRB- (F-13)"},

        # ========================================================
        # WEDNESDAY
        # ========================================================
        # SY(ECT)
        {"day": "Wednesday", "slot": 1, "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "teacher": "SSA", "room": "F-13", "type": "Online", "title": "TH-MDM--IoT-Online SSA/AKS/DJT/ABD-(F-13)", "span": 1},
        {"day": "Wednesday", "slot": 3, "class": "SY(ECT)", "subject": "TH-PCC-NT-203", "teacher": "DR.SLK", "room": "F-12", "type": "Theory", "title": "TH-PCC-NT-203-Dr.SLK (F-12)"},
        {"day": "Wednesday", "slot": 4, "class": "SY(ECT)", "subject": "TH-VEC-CoI-231", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-VEC-CoI-231-Dr.KPP (F-12)"},
        {"day": "Wednesday", "slot": 6, "class": "SY(ECT)", "subject": "TH-OEI-PDE-233", "teacher": "ABD", "room": "F-12", "type": "Theory", "title": "TH-OEI-PDE-233 ABD (F-12)"},
        {"day": "Wednesday", "slot": 7, "class": "SY(ECT)", "subject": "TH-PCC-EDC-202", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-PCC-EDC-202-DJT (F-12)"},
        {"day": "Wednesday", "slot": 9, "class": "SY(ECT)", "batch": "S2", "subject": "PR-NT", "teacher": "MVM", "room": "F-19", "type": "Practical", "title": "PR-S2-NT-F-19(CSL)-MVM", "span": 2},
        {"day": "Wednesday", "slot": 9, "class": "SY(ECT)", "batch": "S4", "subject": "PR-EDC", "teacher": "DJT", "room": "F-18", "type": "Practical", "title": "PR-S4-EDC-F-18(EDCL)-DJT", "span": 2},
        {"day": "Wednesday", "slot": 9, "class": "SY(ECT)", "batch": "S1", "subject": "PR-SL", "teacher": "SSA", "room": "F-20", "type": "Practical", "title": "PR-S1-SL-F-20(ESVL)-SSA", "span": 2},
        {"day": "Wednesday", "slot": 9, "class": "SY(ECT)", "batch": "S2", "subject": "PR-MProj", "teacher": "Dr.MRB", "room": "Lab 14A", "type": "Practical", "title": "PR-S2-MProj-14A(PCB&SL)-Dr.MRB", "span": 2},

        # TY(ECT)
        {"day": "Wednesday", "slot": 3, "class": "TY(ECT)", "batch": "T3", "subject": "PR-DSPL", "teacher": "MVM", "room": "F-14", "type": "Practical", "title": "PR-T3-DSPL-F-14 (CPSL)-MVM", "span": 2},
        {"day": "Wednesday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PCC-AC", "teacher": "SSA", "room": "F-12", "type": "Theory", "title": "TH-PCC-AC-SSA (F-12)"},
        {"day": "Wednesday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PPC-DSP", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-PPC-DSP-Dr.KPP (F-12)"},
        {"day": "Wednesday", "slot": 9, "class": "TY(ECT)", "subject": "TH-OE-XYZ", "teacher": "AKS", "room": "F-12", "type": "Theory", "title": "OE- TH-XYZ-AKS-(F-12)", "span": 2},

        # BY(ECT)
        {"day": "Wednesday", "slot": 3, "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "teacher": "VSJ", "room": "F-13", "type": "Theory", "title": "TH-OEC 4- EWM-VSJ- (F-13)"},
        {"day": "Wednesday", "slot": 4, "class": "BY(ECT)", "subject": "TH-ME-PPC 10", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-ME-PPC 10- PPK (F-13)"},
        {"day": "Wednesday", "slot": 6, "class": "BY(ECT)", "batch": "B3", "subject": "PR-ME", "teacher": "PPK", "room": "F-14A", "type": "Practical", "title": "PR-B3-ME-F-14A(OC&ML)-PPK", "span": 2},
        {"day": "Wednesday", "slot": 9, "class": "BY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-13", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},

        # ========================================================
        # THURSDAY
        # ========================================================
        # SY(ECT)
        {"day": "Thursday", "slot": 1, "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "teacher": "SSA", "room": "F-13", "type": "Online", "title": "TH-MDM--IoT-Online SSA/AKS/DJT/ABD-(F-13)"},
        {"day": "Thursday", "slot": 3, "class": "SY(ECT)", "subject": "TH-PCC-NT-203", "teacher": "DR.SLK", "room": "F-12", "type": "Theory", "title": "TH-PCC-NT-203-Dr.SLK (F-12)"},
        {"day": "Thursday", "slot": 4, "class": "SY(ECT)", "subject": "TH-VEC-CoI-231", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-VEC-CoI-231-Dr.KPP (F-12)"},
        {"day": "Thursday", "slot": 6, "class": "SY(ECT)", "batch": "S1", "subject": "PR-EDC", "teacher": "DJT", "room": "F-18", "type": "Practical", "title": "PR-S1-EDC-F-18(EDCL)-DJT", "span": 2},
        {"day": "Thursday", "slot": 6, "class": "SY(ECT)", "batch": "S2", "subject": "PR-SL", "teacher": "SSA", "room": "F-20", "type": "Practical", "title": "PR-S2-SL-F-20(ESVL)-SSA", "span": 2},
        {"day": "Thursday", "slot": 6, "class": "SY(ECT)", "batch": "S3", "subject": "PR-MProj", "teacher": "Dr.MRB", "room": "Lab 14", "type": "Practical", "title": "PR-S3-MProj-14(PCBL)-Dr.MRB", "span": 2},
        {"day": "Thursday", "slot": 9, "class": "SY(ECT)", "batch": "S1", "subject": "PR-MProj", "teacher": "VSJ", "room": "Lab 14", "type": "Practical", "title": "PR-S1-MProj-14(PCBL)-VSJ", "span": 2},
        {"day": "Thursday", "slot": 9, "class": "SY(ECT)", "batch": "S2", "subject": "PR-NT", "teacher": "MVM", "room": "F-18", "type": "Practical", "title": "PR-S2-NT-F-18(EDCL)-MVM", "span": 2},
        {"day": "Thursday", "slot": 9, "class": "SY(ECT)", "batch": "S3", "subject": "PR-SL", "teacher": "SSA", "room": "F-20", "type": "Practical", "title": "PR-S3-SL-F-20(ESDL)-SSA", "span": 2},

        # TY(ECT)
        {"day": "Thursday", "slot": 1, "class": "TY(ECT)", "subject": "TH-MDM-DSP", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-MDM--DSP-DJT- (F-12)"},
        {"day": "Thursday", "slot": 3, "class": "TY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-12", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},
        {"day": "Thursday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PEC-FoC", "teacher": "PPK", "room": "F-12", "type": "Theory", "title": "TH-PEC-FoC-PPK (F-12)"},
        {"day": "Thursday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PPC-DSP", "teacher": "Dr.KPP", "room": "F-12", "type": "Theory", "title": "TH-PPC-DSP-Dr.KPP (F-12)"},
        {"day": "Thursday", "slot": 9, "class": "TY(ECT)", "batch": "T4", "subject": "PR-ACL", "teacher": "KAP", "room": "F-19", "type": "Practical", "title": "PR-T4-ACL-F-19(CSL)-KAP", "span": 2},

        # BY(ECT)
        {"day": "Thursday", "slot": 3, "class": "BY(ECT)", "subject": "TH-ME-PPC 10", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-ME-PPC 10- PPK (F-13)"},
        {"day": "Thursday", "slot": 4, "class": "BY(ECT)", "subject": "TH-OEC3-MC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "TH-OEC3-MC-SSA- (F-13)"},
        {"day": "Thursday", "slot": 6, "class": "BY(ECT)", "subject": "TH-HSSMC-EE&FM", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-HSSMC-EE&FM-MVM (F-13)"},
        {"day": "Thursday", "slot": 7, "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "teacher": "VSJ", "room": "F-13", "type": "Theory", "title": "TH-OEC 4- EWM-VSJ- (F-13)"},
        {"day": "Thursday", "slot": 9, "class": "BY(ECT)", "batch": "B4", "subject": "PR-ME", "teacher": "PPK", "room": "F-14A", "type": "Practical", "title": "PR-B4-ME-F-14A(OC&ML)-PPK", "span": 2},

        # ========================================================
        # FRIDAY
        # ========================================================
        # SY(ECT)
        {"day": "Friday", "slot": 1, "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "teacher": "SSA", "room": "F-13", "type": "Online", "title": "TH-MDM--IoT-Online SSA/AKS/DJT/ABD-(F-13)"},
        {"day": "Friday", "slot": 3, "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "teacher": "SSP", "room": "F-12", "type": "Theory", "title": "TH-BSC-EM-III-201-SSP (F-12)"},
        {"day": "Friday", "slot": 4, "class": "SY(ECT)", "subject": "TH-HSSM-ED-232", "teacher": "Dr.MRB", "room": "F-12", "type": "Theory", "title": "TH-HSSM-ED-232-Dr.MRB (F-12)"},
        {"day": "Friday", "slot": 6, "class": "SY(ECT)", "batch": "S2", "subject": "PR-EDC", "teacher": "DJT", "room": "F-18", "type": "Practical", "title": "PR-S2-EDC-F-18(EDCL)-DJT", "span": 2},
        {"day": "Friday", "slot": 6, "class": "SY(ECT)", "batch": "S4", "subject": "PR-MProj", "teacher": "Dr.MRB", "room": "Lab 14", "type": "Practical", "title": "PR-S4-MProj-14(PCBL)-Dr.MRB", "span": 2},
        {"day": "Friday", "slot": 9, "class": "SY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-12", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},

        # TY(ECT)
        {"day": "Friday", "slot": 1, "class": "TY(ECT)", "subject": "TH-MDM-DSP", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-MDM--DSP-DJT- (F-12)"},
        {"day": "Friday", "slot": 3, "class": "TY(ECT)", "subject": "TH-OE-XYZ", "teacher": "AKS", "room": "F-13", "type": "Theory", "title": "TH-OE-XYZ-AKS- (F-13)"},
        {"day": "Friday", "slot": 4, "class": "TY(ECT)", "subject": "TH-PCC-EWT", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-PCC-EWT-MVM- (F-13)"},
        {"day": "Friday", "slot": 6, "class": "TY(ECT)", "subject": "TH-PEC-FoC", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-PEC-FoC-PPK (F-13)"},
        {"day": "Friday", "slot": 7, "class": "TY(ECT)", "subject": "TH-PCC-AC", "teacher": "SSA", "room": "F-13", "type": "Theory", "title": "PCC- TH-AC-SSA (F-13)"},
        {"day": "Friday", "slot": 9, "class": "TY(ECT)", "batch": "T3", "subject": "PR-ACL", "teacher": "KAP", "room": "F-19", "type": "Practical", "title": "PR-T3-ACL-F-19(CSL)-KAP", "span": 2},

        # BY(ECT)
        {"day": "Friday", "slot": 3, "class": "BY(ECT)", "batch": "B1", "subject": "PR-ME", "teacher": "PPK", "room": "F-14A", "type": "Practical", "title": "PR-B1-ME-F-14A(OC&ML)-PPK", "span": 2},
        {"day": "Friday", "slot": 3, "class": "BY(ECT)", "batch": "B2", "subject": "PR-MProj3", "teacher": "DJT", "room": "F-17", "type": "Practical", "title": "PR-B2-M.Proj3-F-17(DEML)-DJT", "span": 2},
        {"day": "Friday", "slot": 3, "class": "BY(ECT)", "batch": "B4", "subject": "PR-MProj3", "teacher": "VSJ", "room": "Lab 14A", "type": "Practical", "title": "PR-B4-M.Proj3-14A(PCB&SL)-VSJ", "span": 2},
        {"day": "Friday", "slot": 6, "class": "BY(ECT)", "subject": "TH-OEC 4-EWM", "teacher": "VSJ", "room": "F-13", "type": "Theory", "title": "TH-OEC 4- EWM-VSJ- (F-13)"},
        {"day": "Friday", "slot": 7, "class": "BY(ECT)", "subject": "TH-HSSMC-EE&FM", "teacher": "MVM", "room": "F-12", "type": "Theory", "title": "TH-HSSMC-EE&FM-MVM (F-12)"},
        {"day": "Friday", "slot": 9, "class": "BY(ECT)", "subject": "TH-PEC 4-GA(FOC)", "teacher": "Dr.MRB", "room": "F-13", "type": "Theory", "title": "TH-PEC 4- GA(FOC)-Dr.MRB- (F-13)"},
        {"day": "Friday", "slot": 10, "class": "BY(ECT)", "subject": "TH-ME-PPC 10", "teacher": "PPK", "room": "F-13", "type": "Theory", "title": "TH-ME-PPC 10- PPK (F-13)"},

        # ========================================================
        # SATURDAY
        # ========================================================
        # SY(ECT)
        {"day": "Saturday", "slot": 1, "class": "SY(ECT)", "subject": "TH-MDM-IoT-Online", "teacher": "SSA", "room": "F-13", "type": "Practical", "title": "PR-MDM--IoT-Online SSA/AKS/DJT/ABD-(F-13)"},
        {"day": "Saturday", "slot": 3, "class": "SY(ECT)", "batch": "S2", "subject": "PR-MProj", "teacher": "PPK", "room": "F-19", "type": "Practical", "title": "PR-S2-MProj-F-19(CSL)-PPK", "span": 2},
        {"day": "Saturday", "slot": 3, "class": "SY(ECT)", "batch": "S4", "subject": "PR-SL", "teacher": "SSA", "room": "F-20", "type": "Practical", "title": "PR-S4-SL-F-20(ESVL)-SSA", "span": 2},
        {"day": "Saturday", "slot": 6, "class": "SY(ECT)", "subject": "TH-PCCL-SL-207", "teacher": "SSA", "room": "F-12", "type": "Theory", "title": "TH-PCCL-SL-207-SSA (F-12)"},
        {"day": "Saturday", "slot": 7, "class": "SY(ECT)", "subject": "TH-BSC-EM-III-201", "teacher": "SSP", "room": "F-12", "type": "Theory", "title": "TH-BSC-EM-III-201-SSP (F-12)"},
        {"day": "Saturday", "slot": 9, "class": "SY(ECT)", "batch": "S4", "subject": "PR-MProj", "teacher": "VSJ", "room": "F-19", "type": "Practical", "title": "PR-S4-MProj-F19(CSL)-VSJ", "span": 2},
        {"day": "Saturday", "slot": 9, "class": "SY(ECT)", "batch": "S1", "subject": "PR-MProj", "teacher": "Dr.MRB", "room": "Lab 14A", "type": "Practical", "title": "PR-S1-MProj-14A(PCB&SL)-Dr.MRB", "span": 2},

        # TY(ECT)
        {"day": "Saturday", "slot": 1, "class": "TY(ECT)", "subject": "TH-MDM-DSP", "teacher": "DJT", "room": "F-12", "type": "Theory", "title": "TH-MDM--DSP-DJT- (F-12)"},
        {"day": "Saturday", "slot": 3, "class": "TY(ECT)", "subject": "TH-OE-XYZ", "teacher": "AKS", "room": "F-13", "type": "Theory", "title": "TH-OE-XYZ-AKS- (F-13)"},
        {"day": "Saturday", "slot": 4, "class": "TY(ECT)", "subject": "TH-PCC-EWT", "teacher": "MVM", "room": "F-13", "type": "Theory", "title": "TH-PCC-EWT-MVM- (F-13)"},
        {"day": "Saturday", "slot": 6, "class": "TY(ECT)", "subject": "Mentor-Meeting", "teacher": "SSA", "room": "F-13", "type": "Meeting", "title": "Mentor Mentee Meeting", "span": 2},
        {"day": "Saturday", "slot": 9, "class": "TY(ECT)", "batch": "T4", "subject": "PR-DSPL", "teacher": "MVM", "room": "F-14B", "type": "Practical", "title": "PR-T4-DSPL-F-14B (CP&CL)-MVM", "span": 2},

        # BY(ECT)
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
