import os
import shutil
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file, Response
from functools import wraps
from models import db, User, Teacher, Room, AcademicClass, Batch, Subject, TimeSlot, TimetableEntry, CollegeSetting
from seed_data import seed_database, load_pdf_timetable_entries
from generator import check_all_conflicts, validate_cell_edit, generate_smart_timetable
from pdf_exporter import generate_pdf_timetable

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-timetable-secret-key-2026'

# Support both Local Development and Serverless Deployment (Netlify / AWS Lambda / Render)
import tempfile

IS_SERVERLESS = os.environ.get('NETLIFY') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
if IS_SERVERLESS:
    # On serverless platforms, write to the platform temporary directory (/tmp on Linux/Lambda)
    db_dir = tempfile.gettempdir()
    db_file = os.path.join(db_dir, 'timetable.db')
    # Copy pre-seeded local db to temp directory if it doesn't exist yet
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
            db.create_all()
            seed_database()
        app.db_initialized = True

# Context processor to inject college setting and clash counts into all templates
@app.context_processor
def inject_global_data():
    setting = CollegeSetting.query.first()
    conflicts = check_all_conflicts()
    return dict(
        setting=setting,
        conflict_count=len(conflicts),
        is_logged_in=('user_id' in session),
        current_username=session.get('username')
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
    stats = {
        'teachers': Teacher.query.count(),
        'subjects': Subject.query.count(),
        'classes': AcademicClass.query.count(),
        'rooms': Room.query.count(),
        'entries': TimetableEntry.query.count(),
        'conflicts': len(check_all_conflicts())
    }
    recent_entries = TimetableEntry.query.order_by(TimetableEntry.id.desc()).limit(8).all()
    teachers = Teacher.query.order_by(Teacher.name).all()
    classes = AcademicClass.query.order_by(AcademicClass.id).all()
    rooms = Room.query.order_by(Room.name).all()
    return render_template('dashboard.html', stats=stats, recent_entries=recent_entries, teachers=teachers, classes=classes, rooms=rooms)

# -------------------------------------------------------------
# TIMETABLE VIEWS
# -------------------------------------------------------------
@app.route('/timetable')
def timetable_master():
    """
    Master College Timetable View:
    Displays SY, TY, BY together for all days in the exact format of the college PDF.
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.order_by(TimeSlot.slot_index).all()
    classes = AcademicClass.query.order_by(AcademicClass.id).all()
    teachers = Teacher.query.order_by(Teacher.code).all()
    rooms = Room.query.order_by(Room.name).all()
    subjects = Subject.query.order_by(Subject.code).all()
    batches = Batch.query.order_by(Batch.name).all()

    entries = TimetableEntry.query.all()
    grid = {}
    for day in days:
        grid[day] = {}
        for c in classes:
            grid[day][c.id] = {}
            for s in slots:
                grid[day][c.id][s.id] = []

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

    return render_template(
        'timetable_teacher.html',
        teachers=teachers,
        selected_teacher=selected_teacher,
        days=days,
        slots=slots,
        grid=grid
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
# EDITABLE CELL API (SAVE, UPDATE, DELETE, CONFLICT-CHECK)
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

@app.route('/timetable/generate', methods=['GET', 'POST'])
@login_required
def generate_timetable():
    if request.method == 'POST':
        success = generate_smart_timetable()
        if success:
            flash('Timetable generated successfully using smart clash-free algorithm!', 'success')
        else:
            flash('Failed to generate timetable.', 'danger')
        return redirect(url_for('timetable_master'))
    conflicts = check_all_conflicts()
    return render_template('generate.html', conflicts=conflicts)

# -------------------------------------------------------------
# CONFLICT MATRIX & AUDITOR
# -------------------------------------------------------------
@app.route('/conflicts')
def conflict_report():
    conflicts = check_all_conflicts()
    return render_template('conflict_report.html', conflicts=conflicts)

# -------------------------------------------------------------
# EXPORT / PRINT
# -------------------------------------------------------------
@app.route('/export/pdf')
def export_pdf():
    class_id = request.args.get('class_id', type=int)
    pdf_buffer = generate_pdf_timetable(class_id=class_id)
    filename = f"Timetable_{'All_Classes' if not class_id else AcademicClass.query.get(class_id).name}_2026-27.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

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
# CRUD: TEACHERS
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

        if not name or not code:
            flash('Name and Faculty Code are required.', 'danger')
        elif Teacher.query.filter_by(code=code.strip()).first():
            flash(f'Faculty with code {code} already exists!', 'danger')
        else:
            t = Teacher(name=name.strip(), code=code.strip(), designation=designation, email=email, phone=phone, max_weekly_hours=hours)
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

# -------------------------------------------------------------
# CRUD: SUBJECTS
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# CRUD: ROOMS & LABORATORIES
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# CRUD: CLASSES & BATCHES
# -------------------------------------------------------------
@app.route('/classes', methods=['GET', 'POST'])
@login_required
def classes_list():
    if request.method == 'POST':
        name = request.form.get('name')
        year_name = request.form.get('year_name')
        semester = request.form.get('semester', type=int)
        if not name or not year_name or not semester:
            flash('Class name, year and semester are required.', 'danger')
        elif AcademicClass.query.filter_by(name=name.strip()).first():
            flash(f'Class {name} already exists!', 'danger')
        else:
            c = AcademicClass(name=name.strip(), year_name=year_name.strip(), semester=semester)
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

# -------------------------------------------------------------
# CRUD: TIME SLOTS & RECESS
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# RUN SERVER
# -------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
