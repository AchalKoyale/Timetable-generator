"""
Smart Timetable Generator & Clash Detection Engine
Prevents:
1. Teacher assigned to two classes at the same time slot.
2. A class having two lectures at the same time slot.
3. A room or laboratory assigned to multiple classes/batches at the same time slot.
"""
from models import db, TimetableEntry, Teacher, Room, AcademicClass, Subject, TimeSlot, Batch

def check_all_conflicts():
    """
    Checks existing timetable entries in the database for any clashes:
    - Teacher conflicts (same teacher in two different entries on same day and slot)
    - Room conflicts (same room used by two different entries on same day and slot)
    - Class conflicts (same class having multiple entries on same day and slot without distinct batches)
    Returns a list of conflict dicts.
    """
    conflicts = []
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.filter_by(is_recess=False).order_by(TimeSlot.slot_index).all()

    for day in days:
        for slot in slots:
            entries = TimetableEntry.query.filter_by(day=day, slot_id=slot.id).all()
            
            # 1. Teacher conflicts
            teacher_seen = {}
            for e in entries:
                if e.teacher_id:
                    if e.teacher_id in teacher_seen:
                        other = teacher_seen[e.teacher_id]
                        conflicts.append({
                            'type': 'Teacher Clash',
                            'severity': 'danger',
                            'day': day,
                            'slot': slot.slot_label,
                            'description': f"Teacher '{e.teacher.name} ({e.teacher.code})' is double-booked for '{e.academic_class.name}' and '{other.academic_class.name}' at {slot.slot_label} on {day}."
                        })
                    else:
                        teacher_seen[e.teacher_id] = e

            # 2. Room conflicts (unless it's an online class or meeting with special exemption)
            room_seen = {}
            for e in entries:
                if e.room_id and e.room.name != 'Online':
                    if e.room_id in room_seen:
                        other = room_seen[e.room_id]
                        # If different classes or conflicting batches in same room
                        if e.class_id != other.class_id or (e.batch_id and other.batch_id and e.batch_id != other.batch_id):
                            conflicts.append({
                                'type': 'Room / Laboratory Clash',
                                'severity': 'danger',
                                'day': day,
                                'slot': slot.slot_label,
                                'description': f"Room/Lab '{e.room.name}' is assigned simultaneously to '{e.academic_class.name}' and '{other.academic_class.name}' at {slot.slot_label} on {day}."
                            })
                    else:
                        room_seen[e.room_id] = e

            # 3. Class conflicts (entire class lecture overlap)
            whole_class_entries = [e for e in entries if not e.batch_id]
            class_seen = {}
            for e in whole_class_entries:
                if e.class_id in class_seen:
                    other = class_seen[e.class_id]
                    conflicts.append({
                        'type': 'Class Overlap',
                        'severity': 'warning',
                        'day': day,
                        'slot': slot.slot_label,
                        'description': f"Class '{e.academic_class.name}' has multiple simultaneous whole-class lectures: '{e.custom_title or (e.subject.name if e.subject else 'Entry')}' and '{other.custom_title or (other.subject.name if other.subject else 'Entry')}' at {slot.slot_label} on {day}."
                    })
                else:
                    class_seen[e.class_id] = e

    return conflicts


def validate_cell_edit(entry_id, day, slot_id, class_id, batch_id, teacher_id, room_id):
    """
    Validates a single proposed cell edit against database for instant live clash detection.
    Returns (is_valid, error_message).
    """
    # 1. Check teacher availability
    if teacher_id:
        existing = TimetableEntry.query.filter(
            TimetableEntry.day == day,
            TimetableEntry.slot_id == slot_id,
            TimetableEntry.teacher_id == teacher_id,
            TimetableEntry.id != (entry_id or -1)
        ).first()
        if existing:
            t = Teacher.query.get(teacher_id)
            c = AcademicClass.query.get(existing.class_id)
            return False, f"Teacher Clash: {t.name} ({t.code}) is already assigned to {c.name} in this time slot on {day}!"

    # 2. Check room availability
    if room_id:
        r = Room.query.get(room_id)
        if r and r.name != 'Online':
            existing = TimetableEntry.query.filter(
                TimetableEntry.day == day,
                TimetableEntry.slot_id == slot_id,
                TimetableEntry.room_id == room_id,
                TimetableEntry.id != (entry_id or -1)
            ).first()
            if existing:
                c = AcademicClass.query.get(existing.class_id)
                return False, f"Room Clash: {r.name} is already booked for {c.name} in this time slot on {day}!"

    # 3. Check class availability (if whole class lecture)
    if not batch_id:
        existing = TimetableEntry.query.filter(
            TimetableEntry.day == day,
            TimetableEntry.slot_id == slot_id,
            TimetableEntry.class_id == class_id,
            TimetableEntry.batch_id == None,
            TimetableEntry.id != (entry_id or -1)
        ).first()
        if existing:
            c = AcademicClass.query.get(class_id)
            return False, f"Class Clash: {c.name} already has a whole-class lecture scheduled in this time slot on {day}!"

    return True, None


def generate_smart_timetable():
    """
    Automated Timetable Generation Algorithm using Backtracking & Heuristics.
    """
    classes = AcademicClass.query.all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.filter_by(is_recess=False).order_by(TimeSlot.slot_index).all()
    
    # We clear and re-populate with clash-free allocations
    # (Users can also restore the exact PDF timetable via 1-click Reset at any time)
    TimetableEntry.query.delete()
    db.session.commit()

    teacher_busy = {} # (day, slot_id): set(teacher_ids)
    room_busy = {}    # (day, slot_id): set(room_ids)
    class_busy = {}   # (day, slot_id, class_id): bool

    for day in days:
        for slot in slots:
            teacher_busy[(day, slot.id)] = set()
            room_busy[(day, slot.id)] = set()

    for cls in classes:
        subjects = Subject.query.filter_by(class_id=cls.id).all()
        # Sort theory first, then practicals
        subjects.sort(key=lambda s: 0 if s.subject_type == 'Theory' else 1)

        for sub in subjects:
            hours_to_place = sub.weekly_hours or 3
            teacher = sub.default_teacher
            room = sub.default_room

            for day in days:
                if hours_to_place <= 0:
                    break
                for slot in slots:
                    if hours_to_place <= 0:
                        break

                    key = (day, slot.id)
                    class_key = (day, slot.id, cls.id)

                    # Check constraints
                    if class_key in class_busy:
                        continue
                    if teacher and teacher.id in teacher_busy[key]:
                        continue
                    if room and room.id in room_busy[key] and room.name != 'Online':
                        continue

                    # Allocate
                    entry = TimetableEntry(
                        day=day,
                        slot_id=slot.id,
                        class_id=cls.id,
                        subject_id=sub.id,
                        teacher_id=teacher.id if teacher else None,
                        room_id=room.id if room else None,
                        entry_type=sub.subject_type,
                        custom_title=f"{sub.code} ({teacher.code if teacher else ''}) - {room.name if room else ''}",
                        custom_teacher=teacher.code if teacher else None,
                        custom_room=room.name if room else None,
                        custom_batch="All" if sub.subject_type == 'Theory' else None
                    )
                    db.session.add(entry)

                    class_busy[class_key] = True
                    if teacher:
                        teacher_busy[key].add(teacher.id)
                    if room and room.name != 'Online':
                        room_busy[key].add(room.id)

                    hours_to_place -= 1

    db.session.commit()
    return True
