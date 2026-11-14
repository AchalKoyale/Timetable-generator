import os
import shutil
import csv
import io
import tempfile
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file, Response
from functools import wraps
from models import db, User, Teacher, Room, AcademicClass, Batch, Subject, TimeSlot, TimetableEntry, CollegeSetting, TeacherWorkloadAssignment
from seed_data import seed_database, load_pdf_timetable_entries, migrate_database
from generator import check_all_conflicts, validate_cell_edit, generate_smart_timetable, swap_timetable_entries, move_timetable_entry
from pdf_exporter import generate_pdf_timetable

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-timetable-secret-key-2026'

# Support both Local Development and Serverless Deployment
IS_SERVERLESS = os.environ.get('NETLIFY') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
if IS_SERVERLESS:
    db_dir = tempfile.gettempdir()
    db_file = os.path.join(db_dir, 'timetable.db')
    local_db = os.path.join(os.path.dirname(__file__), 'instance', 'timetable.db')
    if not os.path.exists(local_db):
        local_db = os.path.join(os.path.dirname(__file__), 'timetable.db')
    if not os.path.exists(db_file) and os.path.exists(local_db):
        try:
            shutil.copyfile(local_db, db_file)
        except Exception:
            pass
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file.replace(os.sep, "/")}'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///timetable.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this admin page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def initialize_database():
    if not hasattr(app, 'db_initialized'):
        with app.app_context():
            migrate_database()
            db.create_all()
            seed_database()
        app.db_initialized = True

@app.context_processor
def inject_global_data():
    setting = CollegeSetting.query.first()
    conflicts = check_all_conflicts()
    teachers = Teacher.query.order_by(Teacher.name).all()
    subjects = Subject.query.order_by(Subject.code).all()
    rooms = Room.query.order_by(Room.name).all()
    batches = Batch.query.order_by(Batch.name).all()
    slots = TimeSlot.query.filter_by(is_recess=False).order_by(TimeSlot.slot_index).all()
    classes = AcademicClass.query.order_by(AcademicClass.id).all()
    return dict(
        setting=setting,
        conflict_count=len(conflicts),
        is_logged_in=('user_id' in session),
        current_username=session.get('username'),
        all_teachers=teachers,
        all_subjects=subjects,
        all_rooms=rooms,
        all_batches=batches,
        all_slots=slots,
        all_classes=classes
    )

# -------------------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Default is admin / admin123', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# -------------------------------------------------------------
# DASHBOARD
# -------------------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('timetable_master'))

@app.route('/dashboard')
@login_required
def dashboard():
    teachers = Teacher.query.order_by(Teacher.name).all()
    classes = AcademicClass.query.order_by(AcademicClass.id).all()
    rooms = Room.query.order_by(Room.name).all()
    subjects = Subject.query.order_by(Subject.code).all()
    workloads = TeacherWorkloadAssignment.query.all()
    conflicts = check_all_conflicts()

    total_assigned_hours = sum(w.total_hours for w in workloads)
    total_scheduled_hours = TimetableEntry.query.count()

    stats = {
        'teachers': len(teachers),
        'subjects': len(subjects),
        'classes': len(classes),
        'rooms': len(rooms),
        'entries': total_scheduled_hours,
        'assigned_hours': total_assigned_hours,
        'conflicts': len(conflicts)
    }

    recent_entries = TimetableEntry.query.order_by(TimetableEntry.id.desc()).limit(8).all()
    return render_template(
        'dashboard.html',
        stats=stats,
        recent_entries=recent_entries,
        teachers=teachers,
        classes=classes,
        rooms=rooms,
        workloads=workloads
    )

# -------------------------------------------------------------
# MASTER & FILTERED TIMETABLE VIEWS
# -------------------------------------------------------------
@app.route('/timetable')
def timetable_master():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.order_by(TimeSlot.slot_index).all()
    classes = AcademicClass.query.order_by(AcademicClass.id).all()
    teachers = Teacher.query.order_by(Teacher.code).all()
    rooms = Room.query.order_by(Room.name).all()
    subjects = Subject.query.order_by(Subject.code).all()
    batches = Batch.query.order_by(Batch.name).all()

    entries = TimetableEntry.query.all()
    grid = {day: {c.id: {s.id: [] for s in slots} for c in classes} for day in days}

    for e in entries:
        if e.day in grid and e.class_id in grid[e.day] and e.slot_id in grid[e.day][e.class_id]:
            grid[e.day][e.class_id][e.slot_id].append(e)

    conflicts = check_all_conflicts()
    return render_template(
        'timetable_master.html',
        days=days,
        slots=slots,
        classes=classes,
        grid=grid,
        teachers=teachers,
        rooms=rooms,
        subjects=subjects,
        batches=batches,
        conflicts=conflicts
    )

@app.route('/timetable/class')
def timetable_class():
    class_id = request.args.get('class_id', type=int)
    classes = AcademicClass.query.order_by(AcademicClass.id).all()
    if not class_id and classes:
        class_id = classes[0].id

    selected_class = AcademicClass.query.get(class_id) if class_id else None
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.order_by(TimeSlot.slot_index).all()
    teachers = Teacher.query.order_by(Teacher.code).all()
    rooms = Room.query.order_by(Room.name).all()
    subjects = Subject.query.order_by(Subject.code).all()
    batches = Batch.query.filter_by(class_id=class_id).all() if class_id else []

    entries = TimetableEntry.query.filter_by(class_id=class_id).all() if class_id else []
    grid = {day: {s.id: [] for s in slots} for day in days}
    for e in entries:
        if e.day in grid and e.slot_id in grid[e.day]:
            grid[e.day][e.slot_id].append(e)

    return render_template(
        'timetable_class.html',
        classes=classes,
        selected_class=selected_class,
        days=days,
        slots=slots,
        grid=grid,
        teachers=teachers,
        rooms=rooms,
        subjects=subjects,
        batches=batches
    )

@app.route('/timetable/teacher')
def timetable_teacher():
    teacher_id = request.args.get('teacher_id', type=int)
    teachers = Teacher.query.order_by(Teacher.code).all()
    if not teacher_id and teachers:
        teacher_id = teachers[0].id

    selected_teacher = Teacher.query.get(teacher_id) if teacher_id else None
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.order_by(TimeSlot.slot_index).all()
    
    entries = TimetableEntry.query.filter_by(teacher_id=teacher_id).all() if teacher_id else []
    grid = {day: {s.id: [] for s in slots} for day in days}
    for e in entries:
        if e.day in grid and e.slot_id in grid[e.day]:
            grid[e.day][e.slot_id].append(e)

    workload = TeacherWorkloadAssignment.query.filter_by(teacher_id=teacher_id).all() if teacher_id else []

    return render_template(
        'timetable_teacher.html',
        teachers=teachers,
        selected_teacher=selected_teacher,
        days=days,
        slots=slots,
        grid=grid,
        workload=workload
    )

@app.route('/timetable/room')
def timetable_room():
    room_id = request.args.get('room_id', type=int)
    rooms = Room.query.order_by(Room.name).all()
    if not room_id and rooms:
        room_id = rooms[0].id

    selected_room = Room.query.get(room_id) if room_id else None
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.order_by(TimeSlot.slot_index).all()

    entries = TimetableEntry.query.filter_by(room_id=room_id).all() if room_id else []
    grid = {day: {s.id: [] for s in slots} for day in days}
    for e in entries:
        if e.day in grid and e.slot_id in grid[e.day]:
            grid[e.day][e.slot_id].append(e)

    return render_template(
        'timetable_room.html',
        rooms=rooms,
        selected_room=selected_room,
        days=days,
        slots=slots,
        grid=grid
    )

# -------------------------------------------------------------
# TEACHER WORKLOAD MANAGEMENT & EXCEL IMPORT / EXPORT
# -------------------------------------------------------------
@app.route('/workload')
@login_required
def workload_dashboard():
    teachers = Teacher.query.order_by(Teacher.name).all()
    classes = AcademicClass.query.order_by(AcademicClass.id).all()
    subjects = Subject.query.order_by(Subject.code).all()
    assignments = TeacherWorkloadAssignment.query.order_by(TeacherWorkloadAssignment.teacher_id).all()

    total_theory = sum(a.theory_hours for a in assignments)
    total_practical = sum(a.practical_hours for a in assignments)
    total_overall = sum(a.total_hours for a in assignments)

    return render_template(
        'workload.html',
        teachers=teachers,
        classes=classes,
        subjects=subjects,
        assignments=assignments,
        total_theory=total_theory,
        total_practical=total_practical,
        total_overall=total_overall
    )

@app.route('/workload/add', methods=['POST'])
@login_required
def workload_add():
    teacher_id = request.form.get('teacher_id', type=int)
    class_id = request.form.get('class_id', type=int)
    subject_id = request.form.get('subject_id', type=int)
    theory_hours = request.form.get('theory_hours', 0, type=int)
    practical_hours = request.form.get('practical_hours', 0, type=int)
    notes = request.form.get('notes', '')

    if not teacher_id or not class_id or not subject_id:
        flash('Teacher, Class and Subject are required.', 'danger')
    else:
        tot = theory_hours + practical_hours
        assignment = TeacherWorkloadAssignment(
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            theory_hours=theory_hours,
            practical_hours=practical_hours,
            total_hours=tot,
            notes=notes
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Workload assignment added successfully.', 'success')
    return redirect(url_for('workload_dashboard'))

@app.route('/workload/edit/<int:id>', methods=['POST'])
@login_required
def workload_edit(id):
    a = TeacherWorkloadAssignment.query.get_or_404(id)
    a.teacher_id = request.form.get('teacher_id', a.teacher_id, type=int)
    a.class_id = request.form.get('class_id', a.class_id, type=int)
    a.subject_id = request.form.get('subject_id', a.subject_id, type=int)
    a.theory_hours = request.form.get('theory_hours', a.theory_hours, type=int)
    a.practical_hours = request.form.get('practical_hours', a.practical_hours, type=int)
    a.total_hours = a.theory_hours + a.practical_hours
    a.notes = request.form.get('notes', a.notes)
    db.session.commit()
    flash('Workload assignment updated successfully.', 'success')
    return redirect(url_for('workload_dashboard'))

@app.route('/workload/delete/<int:id>', methods=['POST'])
@login_required
def workload_delete(id):
    a = TeacherWorkloadAssignment.query.get_or_404(id)
    db.session.delete(a)
    db.session.commit()
    flash('Workload assignment removed.', 'info')
    return redirect(url_for('workload_dashboard'))

@app.route('/workload/template')
def workload_template():
    """Generates and downloads a clean Excel (.xlsx) template for teacher workload."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Teacher Workload"

    headers = ["Sr.No", "Faculty Code", "Faculty Name", "Class", "Subject Code", "Subject Name", "Theory Hours", "Practical Hours", "Notes"]
    ws.append(headers)

    # Style header row
    header_fill = PatternFill(start_color="0F2744", end_color="0F2744", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Add sample rows based on actual college workload
    sample_data = [
        [1, "DR.SLK", "Dr. Mr. S. L. KOTGIRE", "SY(ECT)", "TH-PCC-NT-203", "Network Theory", 3, 0, "Vice Principal"],
        [2, "Dr.KPP", "Dr. Mrs. K. P. PAITHANE", "SY(ECT)", "TH-VEC-CoI-231", "Constitution of India", 2, 0, "CoI Theory"],
        [3, "Dr.KPP", "Dr. Mrs. K. P. PAITHANE", "TY(ECT)", "TH-PPC-DSP", "Digital Signal Processing", 4, 0, "DSP Theory"],
        [4, "Dr.KPP", "Dr. Mrs. K. P. PAITHANE", "BY(ECT)", "PR-MProj3", "Major Project-I", 0, 8, "4*2=8 Lab"],
        [5, "Dr.MRB", "Dr. M. R. BANWASKAR", "SY(ECT)", "TH-HSSM-ED-232", "Entrepreneurship Dev", 2, 0, "ED Theory"],
        [6, "VSJ", "Mr. V. S. JADHAV", "BY(ECT)", "TH-OEC 4-EWM", "Electronic Waste Mgmt", 4, 0, "EWM Theory"],
        [7, "PPK", "Ms. P. P. KANADKHEDKAR", "BY(ECT)", "PR-ME", "Microwave Engg", 4, 8, "Theory + Lab"]
    ]
    for row in sample_data:
        ws.append(row)

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="MGM_COE_Teacher_Workload_Template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/workload/upload', methods=['POST'])
@login_required
def workload_upload():
    """Uploads and validates Teacher Workload from Excel (.xlsx) or CSV."""
    file = request.files.get('workload_file')
    if not file or not file.filename:
        flash('Please select an Excel (.xlsx) or CSV file to upload.', 'danger')
        return redirect(url_for('workload_dashboard'))

    filename = file.filename.lower()
    errors = []
    imported_count = 0

    try:
        rows = []
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            wb = openpyxl.load_workbook(file, data_only=True)
            ws = wb.active
            for row in ws.iter_rows(values_only=True):
                if any(row):
                    rows.append(row)
        elif filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.reader(stream)
            for row in csv_reader:
                if any(row):
                    rows.append(row)
        else:
            flash('Invalid file format. Please upload an Excel (.xlsx) or CSV file.', 'danger')
            return redirect(url_for('workload_dashboard'))

        if len(rows) < 2:
            flash('Uploaded file contains no data rows.', 'warning')
            return redirect(url_for('workload_dashboard'))

        # Header detection
        header = [str(c).strip().lower() if c else '' for c in rows[0]]
        
        # Expected column positions:
        # Col 1: Faculty Code, Col 3: Class, Col 4: Subject Code, Col 6: Theory Hours, Col 7: Practical Hours
        for row_idx, r in enumerate(rows[1:], start=2):
            if not any(r):
                continue

            # Support both template format (9 cols) and flexible format
            f_code = str(r[1]).strip() if len(r) > 1 and r[1] is not None else ''
            f_name = str(r[2]).strip() if len(r) > 2 and r[2] is not None else ''
            c_name = str(r[3]).strip() if len(r) > 3 and r[3] is not None else ''
            s_code = str(r[4]).strip() if len(r) > 4 and r[4] is not None else ''
            s_name = str(r[5]).strip() if len(r) > 5 and r[5] is not None else ''
            
            try:
                th_hrs = int(r[6]) if len(r) > 6 and r[6] is not None and str(r[6]).strip() != '' else 0
            except ValueError:
                errors.append(f"Row {row_idx}: Theory Hours '{r[6]}' must be a valid integer.")
                continue

            try:
                pr_hrs = int(r[7]) if len(r) > 7 and r[7] is not None and str(r[7]).strip() != '' else 0
            except ValueError:
                errors.append(f"Row {row_idx}: Practical Hours '{r[7]}' must be a valid integer.")
                continue

            notes = str(r[8]).strip() if len(r) > 8 and r[8] is not None else ''

            if not f_code:
                errors.append(f"Row {row_idx}: Missing Faculty Code.")
                continue

            # Find or auto-create Teacher
            teacher = Teacher.query.filter_by(code=f_code).first()
            if not teacher:
                teacher = Teacher(
                    name=f_name or f"Faculty {f_code}",
                    code=f_code,
                    designation='Assistant Professor',
                    department='Electronics and Telecommunication Engineering',
                    max_weekly_hours=20
                )
                db.session.add(teacher)
                db.session.flush()

            # Find or auto-create Class
            academic_class = AcademicClass.query.filter_by(name=c_name).first() if c_name else None
            if not academic_class and c_name:
                academic_class = AcademicClass(name=c_name, year_name=c_name, semester=3)
                db.session.add(academic_class)
                db.session.flush()
            elif not academic_class:
                academic_class = AcademicClass.query.first()

            # Find or auto-create Subject
            subject = Subject.query.filter_by(code=s_code).first() if s_code else None
            if not subject and s_code:
                subject = Subject(
                    code=s_code,
                    name=s_name or s_code,
                    subject_type='Practical' if pr_hrs > 0 and th_hrs == 0 else 'Theory',
                    class_id=academic_class.id if academic_class else None,
                    default_teacher_id=teacher.id,
                    weekly_hours=th_hrs + pr_hrs
                )
                db.session.add(subject)
                db.session.flush()
            elif not subject:
                errors.append(f"Row {row_idx}: Subject code required.")
                continue

            tot = th_hrs + pr_hrs
            assignment = TeacherWorkloadAssignment(
                teacher_id=teacher.id,
                class_id=academic_class.id,
                subject_id=subject.id,
                theory_hours=th_hrs,
                practical_hours=pr_hrs,
                total_hours=tot,
                notes=notes
            )
            db.session.add(assignment)
            imported_count += 1

        db.session.commit()

        if errors:
            flash(f"Imported {imported_count} workload records with {len(errors)} error(s): " + "; ".join(errors[:4]), 'warning')
        else:
            flash(f"Successfully uploaded and validated {imported_count} teacher workload assignments!", 'success')

    except Exception as e:
        db.session.rollback()
        flash(f"Error processing workload file: {str(e)}", 'danger')

    return redirect(url_for('workload_dashboard'))

# -------------------------------------------------------------
# EDITABLE TIMETABLE API & SWAP / MOVE ACTIONS
# -------------------------------------------------------------
@app.route('/api/timetable/entry', methods=['POST'])
@login_required
def save_timetable_entry():
    data = request.get_json() or {}
    entry_id = data.get('entry_id')
    day = data.get('day')
    slot_id = data.get('slot_id')
    class_id = data.get('class_id')
    batch_id = data.get('batch_id') or None
    subject_id = data.get('subject_id') or None
    teacher_id = data.get('teacher_id') or None
    room_id = data.get('room_id') or None
    entry_type = data.get('entry_type', 'Theory')
    custom_title = data.get('custom_title')
    force_save = data.get('force_save', False)

    if not day or not slot_id or not class_id:
        return jsonify({'success': False, 'message': 'Day, Time Slot and Class are required.'}), 400

    is_valid, clash_msg = validate_cell_edit(entry_id, day, slot_id, class_id, batch_id, teacher_id, room_id)
    if not is_valid and not force_save:
        return jsonify({
            'success': False,
            'has_conflict': True,
            'message': clash_msg
        }), 409

    if entry_id:
        entry = TimetableEntry.query.get(entry_id)
        if not entry:
            return jsonify({'success': False, 'message': 'Entry not found.'}), 404
    else:
        entry = TimetableEntry()
        db.session.add(entry)

    entry.day = day
    entry.slot_id = slot_id
    entry.class_id = class_id
    entry.batch_id = batch_id if batch_id else None
    entry.subject_id = subject_id if subject_id else None
    entry.teacher_id = teacher_id if teacher_id else None
    entry.room_id = room_id if room_id else None
    entry.entry_type = entry_type
    
    t_obj = Teacher.query.get(teacher_id) if teacher_id else None
    r_obj = Room.query.get(room_id) if room_id else None
    s_obj = Subject.query.get(subject_id) if subject_id else None
    b_obj = Batch.query.get(batch_id) if batch_id else None

    if custom_title and custom_title.strip():
        entry.custom_title = custom_title.strip()
    else:
        prefix = 'PR' if entry_type == 'Practical' else ('TH' if entry_type == 'Theory' else entry_type)
        b_str = f"-{b_obj.name}" if b_obj else ""
        s_str = s_obj.code if s_obj else "Subject"
        t_str = f"-{t_obj.code}" if t_obj else ""
        r_str = f"({r_obj.name})" if r_obj else ""
        entry.custom_title = f"{prefix}{b_str}-{s_str}{t_str} {r_str}".strip()

    entry.custom_teacher = t_obj.code if t_obj else None
    entry.custom_room = r_obj.name if r_obj else None
    entry.custom_batch = b_obj.name if b_obj else ("All" if entry_type == 'Theory' else None)

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Timetable cell updated successfully!',
        'entry_id': entry.id,
        'display_title': entry.custom_title
    })

@app.route('/api/timetable/entry/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_timetable_entry(entry_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Entry deleted successfully.'})

@app.route('/api/timetable/swap', methods=['POST'])
@login_required
def api_swap_entries():
    """Swaps two lecture entries with collision validation."""
    data = request.get_json() or {}
    e1_id = data.get('entry_id_1')
    e2_id = data.get('entry_id_2')
    if not e1_id or not e2_id:
        return jsonify({'success': False, 'message': 'Both entry IDs are required to swap.'}), 400

    ok, msg = swap_timetable_entries(e1_id, e2_id)
    return jsonify({'success': ok, 'message': msg}), (200 if ok else 409)

@app.route('/api/timetable/move', methods=['POST'])
@login_required
def api_move_entry():
    """Moves a lecture entry to a new slot with collision validation."""
    data = request.get_json() or {}
    entry_id = data.get('entry_id')
    new_day = data.get('new_day')
    new_slot_id = data.get('new_slot_id')

    if not entry_id or not new_day or not new_slot_id:
        return jsonify({'success': False, 'message': 'Entry ID, day and slot ID are required.'}), 400

    ok, msg = move_timetable_entry(entry_id, new_day, new_slot_id)
    return jsonify({'success': ok, 'message': msg}), (200 if ok else 409)

# -------------------------------------------------------------
# TIMETABLE GENERATION & RESET
# -------------------------------------------------------------
@app.route('/timetable/generate', methods=['GET', 'POST'])
@login_required
def generate_timetable():
    if request.method == 'POST':
        target_class_id = request.form.get('class_id', type=int)
        target_day = request.form.get('day')
        if target_class_id == 0:
            target_class_id = None
        if target_day == 'All':
            target_day = None

        ok, msg = generate_smart_timetable(target_class_id=target_class_id, target_day=target_day)
        if ok:
            flash(msg, 'success')
        else:
            flash(msg, 'danger')
        return redirect(url_for('timetable_master'))

    classes = AcademicClass.query.all()
    conflicts = check_all_conflicts()
    return render_template('generate.html', classes=classes, conflicts=conflicts)

@app.route('/timetable/reset', methods=['POST'])
@login_required
def reset_timetable():
    TimetableEntry.query.delete()
    db.session.commit()

    class_map = {c.name: c for c in AcademicClass.query.all()}
    batch_map = {b.name: b for b in Batch.query.all()}
    teacher_map = {t.code: t for t in Teacher.query.all()}
    room_map = {r.name: r for r in Room.query.all()}
    slot_map = {s.slot_index: s for s in TimeSlot.query.all()}
    subject_map = {s.code: s for s in Subject.query.all()}

    load_pdf_timetable_entries(class_map, batch_map, teacher_map, room_map, slot_map, subject_map)
    db.session.commit()
    flash('Timetable has been successfully reset to the official college PDF schedule!', 'success')
    return redirect(url_for('timetable_master'))

@app.route('/conflicts')
def conflict_report():
    conflicts = check_all_conflicts()
    return render_template('conflict_report.html', conflicts=conflicts)

# -------------------------------------------------------------
# EXPORT / PRINT (PDF, EXCEL, CSV)
# -------------------------------------------------------------
@app.route('/export/pdf')
def export_pdf():
    class_id = request.args.get('class_id', type=int)
    pdf_buffer = generate_pdf_timetable(class_id=class_id)
    cls_name = AcademicClass.query.get(class_id).name if class_id else 'All_Classes'
    filename = f"Timetable_{cls_name}_MGM_COE_2026.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/export/excel')
def export_excel():
    """Generates a professional, formatted Excel (.xlsx) Timetable."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Master Timetable"

    setting = CollegeSetting.query.first()
    trust_name = setting.trust_name if setting and setting.trust_name else "Mahatma Gandhi Mission's"
    college_name = setting.college_name if setting and setting.college_name else "COLLEGE OF ENGINEERING"
    title = f"{trust_name} - {college_name}"
    dept = setting.department_name if setting and setting.department_name else "DEPARTMENT OF ELECTRONICS AND TELECOMMUNICATION ENGINEERING"
    wef = setting.wef_date if setting and setting.wef_date else "17/08/2026"
    acad_yr = setting.academic_year if setting and setting.academic_year else "ACADEMIC YEAR 2026-27"
    meta = f"{acad_yr} | WEF: {wef}"

    # Header styling
    ws.merge_cells("A1:K1")
    ws["A1"] = title
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="0F2744")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A2:K2")
    ws["A2"] = dept
    ws["A2"].font = Font(name="Calibri", size=11, bold=True, color="333333")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A3:K3")
    ws["A3"] = meta
    ws["A3"].font = Font(name="Calibri", size=10, italic=True, color="666666")
    ws["A3"].alignment = Alignment(horizontal="center", vertical="center")

    # Table columns
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.order_by(TimeSlot.slot_index).all()
    classes = AcademicClass.query.order_by(AcademicClass.id).all()

    col_headers = ["Day", "Class"] + [s.slot_label for s in slots]
    ws.append([])
    ws.append(col_headers)

    header_row = 5
    for c_idx in range(1, len(col_headers) + 1):
        c = ws.cell(row=header_row, column=c_idx)
        c.fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
        c.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    curr_row = 6
    for day in days:
        for cls in classes:
            row_data = [day, cls.name]
            for s in slots:
                if s.is_recess:
                    row_data.append("RECESS")
                else:
                    entries = TimetableEntry.query.filter_by(day=day, class_id=cls.id, slot_id=s.id).all()
                    if entries:
                        texts = [e.custom_title or (e.subject.code if e.subject else '') for e in entries]
                        row_data.append("\n".join(texts))
                    else:
                        row_data.append("-")
            ws.append(row_data)
            curr_row += 1

    # Formatting widths
    for col in ws.columns:
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="MGM_COE_College_Timetable_2026.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/export/csv')
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Day', 'Time Slot', 'Class', 'Batch', 'Subject Code', 'Subject Name', 'Teacher Code', 'Teacher Name', 'Room / Lab', 'Type', 'Cell Display'])

    entries = TimetableEntry.query.order_by(TimetableEntry.day, TimetableEntry.slot_id).all()
    for e in entries:
        writer.writerow([
            e.day,
            e.slot.slot_label if e.slot else '',
            e.academic_class.name if e.academic_class else '',
            e.batch.name if e.batch else 'All',
            e.subject.code if e.subject else '',
            e.subject.name if e.subject else '',
            e.teacher.code if e.teacher else '',
            e.teacher.name if e.teacher else '',
            e.room.name if e.room else '',
            e.entry_type,
            e.custom_title or ''
        ])

    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=college_timetable_2026.csv'})

# -------------------------------------------------------------
# CRUD: TEACHERS, SUBJECTS, ROOMS, CLASSES, SLOTS
# -------------------------------------------------------------
@app.route('/teachers', methods=['GET', 'POST'])
@login_required
def teachers_list():
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        designation = request.form.get('designation')
        email = request.form.get('email')
        phone = request.form.get('phone')
        hours = request.form.get('max_weekly_hours', type=int, default=20)
        daily_max = request.form.get('max_daily_lectures', type=int, default=3)
        day_off = request.form.get('day_off')
        is_avail = 'is_available' in request.form

        if not name or not code:
            flash('Name and Faculty Code are required.', 'danger')
        elif Teacher.query.filter_by(code=code.strip()).first():
            flash(f'Faculty with code {code} already exists!', 'danger')
        else:
            t = Teacher(
                name=name.strip(),
                code=code.strip(),
                designation=designation,
                email=email,
                phone=phone,
                max_weekly_hours=hours,
                max_daily_lectures=daily_max,
                day_off=day_off if day_off != 'None' else None,
                is_available=is_avail
            )
            db.session.add(t)
            db.session.commit()
            flash(f'Teacher {name} added successfully.', 'success')
        return redirect(url_for('teachers_list'))

    teachers = Teacher.query.order_by(Teacher.name).all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/teachers/edit/<int:id>', methods=['POST'])
@login_required
def teacher_edit(id):
    t = Teacher.query.get_or_404(id)
    t.name = request.form.get('name', t.name).strip()
    t.code = request.form.get('code', t.code).strip()
    t.designation = request.form.get('designation', t.designation)
    t.email = request.form.get('email', t.email)
    t.phone = request.form.get('phone', t.phone)
    t.max_weekly_hours = request.form.get('max_weekly_hours', t.max_weekly_hours, type=int)
    t.max_daily_lectures = request.form.get('max_daily_lectures', t.max_daily_lectures or 3, type=int)
    d_off = request.form.get('day_off')
    t.day_off = d_off if d_off != 'None' else None
    t.is_available = 'is_available' in request.form
    db.session.commit()
    flash(f'Teacher {t.name} updated successfully.', 'success')
    return redirect(url_for('teachers_list'))

@app.route('/teachers/delete/<int:id>', methods=['POST'])
@login_required
def teacher_delete(id):
    t = Teacher.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    flash('Teacher deleted successfully.', 'info')
    return redirect(url_for('teachers_list'))

@app.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects_list():
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        subject_type = request.form.get('subject_type', 'Theory')
        class_id = request.form.get('class_id', type=int)
        default_teacher_id = request.form.get('default_teacher_id', type=int)
        default_room_id = request.form.get('default_room_id', type=int)
        weekly_hours = request.form.get('weekly_hours', 4, type=int)

        if not code or not name:
            flash('Subject code and name are required.', 'danger')
        else:
            s = Subject(
                code=code.strip(),
                name=name.strip(),
                subject_type=subject_type,
                class_id=class_id,
                default_teacher_id=default_teacher_id if default_teacher_id else None,
                default_room_id=default_room_id if default_room_id else None,
                weekly_hours=weekly_hours
            )
            db.session.add(s)
            db.session.commit()
            flash(f'Subject {code} added successfully.', 'success')
        return redirect(url_for('subjects_list'))

    subjects = Subject.query.order_by(Subject.code).all()
    classes = AcademicClass.query.order_by(AcademicClass.name).all()
    teachers = Teacher.query.order_by(Teacher.name).all()
    rooms = Room.query.order_by(Room.name).all()
    return render_template('subjects.html', subjects=subjects, classes=classes, teachers=teachers, rooms=rooms)

@app.route('/subjects/edit/<int:id>', methods=['POST'])
@login_required
def subject_edit(id):
    s = Subject.query.get_or_404(id)
    s.code = request.form.get('code', s.code).strip()
    s.name = request.form.get('name', s.name).strip()
    s.subject_type = request.form.get('subject_type', s.subject_type)
    s.class_id = request.form.get('class_id', s.class_id, type=int)
    t_id = request.form.get('default_teacher_id', type=int)
    s.default_teacher_id = t_id if t_id else None
    r_id = request.form.get('default_room_id', type=int)
    s.default_room_id = r_id if r_id else None
    s.weekly_hours = request.form.get('weekly_hours', s.weekly_hours, type=int)
    db.session.commit()
    flash(f'Subject {s.code} updated successfully.', 'success')
    return redirect(url_for('subjects_list'))

@app.route('/subjects/delete/<int:id>', methods=['POST'])
@login_required
def subject_delete(id):
    s = Subject.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash('Subject deleted successfully.', 'info')
    return redirect(url_for('subjects_list'))

@app.route('/classrooms', methods=['GET', 'POST'])
@login_required
def classrooms_list():
    if request.method == 'POST':
        name = request.form.get('name')
        short_code = request.form.get('short_code')
        room_type = request.form.get('room_type', 'Classroom')
        capacity = request.form.get('capacity', 60, type=int)
        location = request.form.get('location', '')

        if not name:
            flash('Room / Lab name is required.', 'danger')
        elif Room.query.filter_by(name=name.strip()).first():
            flash(f'Room with name {name} already exists!', 'danger')
        else:
            r = Room(name=name.strip(), short_code=short_code or name, room_type=room_type, capacity=capacity, location=location)
            db.session.add(r)
            db.session.commit()
            flash(f'Room/Lab {name} added successfully.', 'success')
        return redirect(url_for('classrooms_list'))

    rooms = Room.query.order_by(Room.name).all()
    return render_template('classrooms.html', rooms=rooms)

@app.route('/classrooms/edit/<int:id>', methods=['POST'])
@login_required
def classroom_edit(id):
    r = Room.query.get_or_404(id)
    r.name = request.form.get('name', r.name).strip()
    r.short_code = request.form.get('short_code', r.short_code)
    r.room_type = request.form.get('room_type', r.room_type)
    r.capacity = request.form.get('capacity', r.capacity, type=int)
    r.location = request.form.get('location', r.location)
    db.session.commit()
    flash(f'Room {r.name} updated successfully.', 'success')
    return redirect(url_for('classrooms_list'))

@app.route('/classrooms/delete/<int:id>', methods=['POST'])
@login_required
def classroom_delete(id):
    r = Room.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    flash('Room/Lab deleted successfully.', 'info')
    return redirect(url_for('classrooms_list'))

@app.route('/classes', methods=['GET', 'POST'])
@login_required
def classes_list():
    if request.method == 'POST':
        name = request.form.get('name')
        year_name = request.form.get('year_name')
        semester = request.form.get('semester', type=int)
        dept = request.form.get('department', 'Electronics and Telecommunication Engineering')
        if not name or not year_name or not semester:
            flash('Class name, year and semester are required.', 'danger')
        elif AcademicClass.query.filter_by(name=name.strip()).first():
            flash(f'Class {name} already exists!', 'danger')
        else:
            c = AcademicClass(name=name.strip(), year_name=year_name.strip(), semester=semester, department=dept)
            db.session.add(c)
            db.session.commit()
            flash(f'Class {name} added successfully.', 'success')
        return redirect(url_for('classes_list'))

    classes = AcademicClass.query.order_by(AcademicClass.id).all()
    return render_template('classes.html', classes=classes)

@app.route('/batches/add', methods=['POST'])
@login_required
def batch_add():
    class_id = request.form.get('class_id', type=int)
    name = request.form.get('name')
    roll_range = request.form.get('roll_range', '1-20')
    if class_id and name:
        b = Batch(class_id=class_id, name=name.strip(), roll_range=roll_range.strip())
        db.session.add(b)
        db.session.commit()
        flash(f'Batch {name} added successfully.', 'success')
    return redirect(url_for('classes_list'))

@app.route('/batches/delete/<int:id>', methods=['POST'])
@login_required
def batch_delete(id):
    b = Batch.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    flash('Batch deleted.', 'info')
    return redirect(url_for('classes_list'))

@app.route('/timeslots', methods=['GET', 'POST'])
@login_required
def timeslots_list():
    if request.method == 'POST':
        slot_index = request.form.get('slot_index', type=int)
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        slot_label = request.form.get('slot_label')
        is_recess = 'is_recess' in request.form
        recess_label = request.form.get('recess_label')

        ts = TimeSlot(
            slot_index=slot_index,
            start_time=start_time,
            end_time=end_time,
            slot_label=slot_label,
            is_recess=is_recess,
            recess_label=recess_label
        )
        db.session.add(ts)
        db.session.commit()
        flash('Time slot added successfully.', 'success')
        return redirect(url_for('timeslots_list'))

    slots = TimeSlot.query.order_by(TimeSlot.slot_index).all()
    return render_template('timeslots.html', slots=slots)

if __name__ == '__main__':
    with app.app_context():
        migrate_database()
        db.create_all()
        seed_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
