from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin') # admin, faculty, viewer
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False) # e.g. DR.SLK, Dr.KPP, DJT
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    designation = db.Column(db.String(100), default='Assistant Professor')
    department = db.Column(db.String(100), default='Electronics and Telecommunication Engineering')
    max_weekly_hours = db.Column(db.Integer, default=20)
    max_daily_lectures = db.Column(db.Integer, default=3) # Prevent same teacher burnout in a single day
    day_off = db.Column(db.String(20), nullable=True) # Preferred day off or half day
    is_available = db.Column(db.Boolean, default=True)

    # Relationships
    timetable_entries = db.relationship('TimetableEntry', backref='teacher', cascade='all, delete-orphan', lazy=True)

    @property
    def total_assigned_workload(self):
        assignments = TeacherWorkloadAssignment.query.filter_by(teacher_id=self.id).all()
        return sum(a.total_hours for a in assignments)

    @property
    def current_scheduled_hours(self):
        return TimetableEntry.query.filter_by(teacher_id=self.id).count()


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g. F-12, F-13, F-14A(OC&ML)
    short_code = db.Column(db.String(30), nullable=True) # e.g. F-12, OC&ML, CSL
    room_type = db.Column(db.String(20), default='Classroom') # 'Classroom' or 'Laboratory'
    capacity = db.Column(db.Integer, default=60)
    location = db.Column(db.String(100), default='First Floor / MGM COE')

    timetable_entries = db.relationship('TimetableEntry', backref='room', cascade='all, delete-orphan', lazy=True)


class AcademicClass(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g. SY(ECT), TY(ECT), BY(ECT)
    year_name = db.Column(db.String(50), nullable=False) # Second Year, Third Year, Final Year
    semester = db.Column(db.Integer, nullable=False) # 3, 5, 7
    department = db.Column(db.String(100), default='Electronics and Telecommunication Engineering')

    batches = db.relationship('Batch', backref='academic_class', cascade='all, delete-orphan', lazy=True)
    subjects = db.relationship('Subject', backref='academic_class', cascade='all, delete-orphan', lazy=True)
    timetable_entries = db.relationship('TimetableEntry', backref='academic_class', cascade='all, delete-orphan', lazy=True)


class Batch(db.Model):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    name = db.Column(db.String(20), nullable=False) # S1, S2, S3, S4, T1, etc.
    roll_range = db.Column(db.String(50), default='1-20') # 1-20, 21-40, 41-60, 61 Onwards

    timetable_entries = db.relationship('TimetableEntry', backref='batch', lazy=True)


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False) # e.g. PCC-EDC-202, BSC-EM-III-201
    name = db.Column(db.String(150), nullable=False)
    subject_type = db.Column(db.String(30), default='Theory') # 'Theory', 'Practical', 'Minor', 'Meeting'
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    default_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    default_room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    weekly_hours = db.Column(db.Integer, default=4)

    default_teacher = db.relationship('Teacher', foreign_keys=[default_teacher_id])
    default_room = db.relationship('Room', foreign_keys=[default_room_id])
    timetable_entries = db.relationship('TimetableEntry', backref='subject', cascade='all, delete-orphan', lazy=True)


class TeacherWorkloadAssignment(db.Model):
    __tablename__ = 'teacher_workload_assignments'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    theory_hours = db.Column(db.Integer, default=0)
    practical_hours = db.Column(db.Integer, default=0)
    total_hours = db.Column(db.Integer, default=0)
    notes = db.Column(db.String(150), nullable=True) # e.g. "4*2=8", "Lab batches", roles

    teacher = db.relationship('Teacher', backref='workload_assignments')
    academic_class = db.relationship('AcademicClass', backref='workload_assignments')
    subject = db.relationship('Subject', backref='workload_assignments')


class TimeSlot(db.Model):
    __tablename__ = 'timeslots'
    id = db.Column(db.Integer, primary_key=True)
    slot_index = db.Column(db.Integer, nullable=False) # 1, 2, 3...
    start_time = db.Column(db.String(10), nullable=False) # '08:00', '10:30'
    end_time = db.Column(db.String(10), nullable=False) # '10:00', '11:30'
    slot_label = db.Column(db.String(50), nullable=False) # '08:00 TO 09:00 Or 10:00', '10:30 TO 11:30'
    is_recess = db.Column(db.Boolean, default=False)
    recess_label = db.Column(db.String(50), nullable=True) # 'Recess', 'Lunch Break'


class TimetableEntry(db.Model):
    __tablename__ = 'timetable_entries'
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False) # 'Monday', 'Tuesday', ...
    slot_id = db.Column(db.Integer, db.ForeignKey('timeslots.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True) # Null for entire class
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    
    # Custom / override fields for rich academic timetable representations
    entry_type = db.Column(db.String(30), default='Theory') # 'Theory', 'Practical', 'Meeting', 'Online'
    custom_title = db.Column(db.String(200), nullable=True) # For complex multi-batch or meeting cells
    custom_teacher = db.Column(db.String(100), nullable=True) # E.g. 'SSA/AKS/DJT/ABD'
    custom_room = db.Column(db.String(100), nullable=True)
    custom_batch = db.Column(db.String(50), nullable=True) # E.g. 'S1', 'S2', 'All'
    span_slots = db.Column(db.Integer, default=1) # 1 or 2 slots duration (e.g. 2 hr practicals)
    
    slot = db.relationship('TimeSlot', backref='entries')


class CollegeSetting(db.Model):
    __tablename__ = 'college_settings'
    id = db.Column(db.Integer, primary_key=True)
    trust_name = db.Column(db.String(200), default="Mahatma Gandhi Mission's")
    college_name = db.Column(db.String(200), default="COLLEGE OF ENGINEERING")
    address = db.Column(db.String(300), default="Near Airport, Off Hingoli Road, Nanded-431605. (An Autonomous Institute, Accredited by NAAC & NBA)")
    department_name = db.Column(db.String(200), default="DEPARTMENT OF ELECTRONICS AND TELECOMMUNICATION ENGINEERING")
    academic_year = db.Column(db.String(50), default="ACADEMIC YEAR 2026-27 (SEMESTER-I) TIME TABLE")
    sem_start_date = db.Column(db.String(50), default="10/08/2026")
    wef_date = db.Column(db.String(50), default="17/08/2026")
    tt_incharge = db.Column(db.String(100), default="Mr. Sayed Shoaib Anwar")
    dept_coordinator = db.Column(db.String(100), default="Ms. A. K. Salve")
    hod_name = db.Column(db.String(100), default="Dr. Mrs. Kalpana P. Paithane")
