"""
Smart Timetable Generator & Intelligent Constraint-Satisfaction Engine
Autonomous Engineering College Timetable Management System

Features:
1. Intelligent Teacher Workload Distribution across Monday to Saturday (no overload on single day).
2. Max daily lecture caps per teacher (e.g. max 2-3 lectures/day).
3. Subject spacing (max 1 theory lecture of the same subject per day).
4. Consecutive 2-hour practical lab scheduling.
5. Absolute clash prevention (Teacher, Classroom, Lab, Class).
6. Targeted regeneration by Class/Division or by Day.
7. Lecture swapping and moving with live collision checking.
8. Constraint diagnostic reporter if generation fails.
"""

import math
from models import db, TimetableEntry, Teacher, Room, AcademicClass, Subject, TimeSlot, Batch, TeacherWorkloadAssignment

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

def check_all_conflicts():
    """
    Checks all timetable entries in the database for clashes:
    - Teacher conflicts (same teacher scheduled twice at same day and slot)
    - Room/Lab conflicts (same room double-booked at same day and slot)
    - Class lecture overlap (whole class scheduled twice at same day and slot)
    """
    conflicts = []
    slots = TimeSlot.query.filter_by(is_recess=False).order_by(TimeSlot.slot_index).all()

    for day in DAYS_OF_WEEK:
        for slot in slots:
            entries = TimetableEntry.query.filter_by(day=day, slot_id=slot.id).all()

            # 1. Teacher conflicts
            teacher_seen = {}
            for e in entries:
                if e.teacher_id:
                    if e.teacher_id in teacher_seen:
                        other = teacher_seen[e.teacher_id]
                        # Conflicting if assigned to two different classes or two whole-class theory lectures
                        if e.class_id != other.class_id or (not e.batch_id and not other.batch_id):
                            t_name = e.teacher.name if e.teacher else f"Teacher #{e.teacher_id}"
                            c1_name = e.academic_class.name if e.academic_class else "Class 1"
                            c2_name = other.academic_class.name if other.academic_class else "Class 2"
                            conflicts.append({
                                'type': 'Teacher Clash',
                                'severity': 'danger',
                                'day': day,
                                'slot': slot.slot_label,
                                'description': f"Teacher '{t_name}' is double-booked for '{c1_name}' and '{c2_name}' at {slot.slot_label} on {day}."
                            })
                    else:
                        teacher_seen[e.teacher_id] = e

            # 2. Room / Laboratory conflicts
            room_seen = {}
            for e in entries:
                if e.room_id and e.room and e.room.name != 'Online':
                    if e.room_id in room_seen:
                        other = room_seen[e.room_id]
                        # Conflicting if different classes or conflicting batches
                        if e.class_id != other.class_id or (e.batch_id and other.batch_id and e.batch_id != other.batch_id):
                            r_name = e.room.name
                            c1_name = e.academic_class.name if e.academic_class else "Class 1"
                            c2_name = other.academic_class.name if other.academic_class else "Class 2"
                            conflicts.append({
                                'type': 'Room / Lab Clash',
                                'severity': 'danger',
                                'day': day,
                                'slot': slot.slot_label,
                                'description': f"Room/Lab '{r_name}' is assigned simultaneously to '{c1_name}' and '{c2_name}' at {slot.slot_label} on {day}."
                            })
                    else:
                        room_seen[e.room_id] = e

            # 3. Class overlap (multiple whole-class lectures)
            whole_class = [e for e in entries if not e.batch_id]
            class_seen = {}
            for e in whole_class:
                if e.class_id in class_seen:
                    other = class_seen[e.class_id]
                    c_name = e.academic_class.name if e.academic_class else f"Class #{e.class_id}"
                    conflicts.append({
                        'type': 'Class Overlap',
                        'severity': 'warning',
                        'day': day,
                        'slot': slot.slot_label,
                        'description': f"Class '{c_name}' has multiple whole-class lectures scheduled at {slot.slot_label} on {day}."
                    })
                else:
                    class_seen[e.class_id] = e

    return conflicts


def validate_cell_edit(entry_id, day, slot_id, class_id, batch_id, teacher_id, room_id, ignore_ids=None):
    """
    Validates a single proposed cell edit against the database for instant collision prevention.
    """
    if ignore_ids is None:
        ignore_ids = [entry_id] if entry_id else []
    elif entry_id and entry_id not in ignore_ids:
        ignore_ids = list(ignore_ids) + [entry_id]

    if teacher_id:
        q = TimetableEntry.query.filter(
            TimetableEntry.day == day,
            TimetableEntry.slot_id == slot_id,
            TimetableEntry.teacher_id == teacher_id
        )
        if ignore_ids:
            q = q.filter(~TimetableEntry.id.in_(ignore_ids))
        existing = q.first()
        if existing:
            t = Teacher.query.get(teacher_id)
            c = AcademicClass.query.get(existing.class_id)
            return False, f"Teacher Clash: {t.name} ({t.code}) is already scheduled for {c.name} at this time on {day}!"

    if room_id:
        r = Room.query.get(room_id)
        if r and r.name != 'Online':
            q = TimetableEntry.query.filter(
                TimetableEntry.day == day,
                TimetableEntry.slot_id == slot_id,
                TimetableEntry.room_id == room_id
            )
            if ignore_ids:
                q = q.filter(~TimetableEntry.id.in_(ignore_ids))
            existing = q.first()
            if existing:
                c = AcademicClass.query.get(existing.class_id)
                return False, f"Room Clash: {r.name} is already booked for {c.name} at this time on {day}!"

    if not batch_id:
        q = TimetableEntry.query.filter(
            TimetableEntry.day == day,
            TimetableEntry.slot_id == slot_id,
            TimetableEntry.class_id == class_id,
            TimetableEntry.batch_id == None
        )
        if ignore_ids:
            q = q.filter(~TimetableEntry.id.in_(ignore_ids))
        existing = q.first()
        if existing:
            c = AcademicClass.query.get(class_id)
            return False, f"Class Clash: {c.name} already has a whole-class lecture scheduled at this time on {day}!"

    return True, None


def swap_timetable_entries(entry_id_1, entry_id_2):
    """
    Swaps the day and slot of two timetable entries with conflict checking.
    """
    e1 = TimetableEntry.query.get(entry_id_1)
    e2 = TimetableEntry.query.get(entry_id_2)
    if not e1 or not e2:
        return False, "One or both entries not found."

    day1, slot1 = e1.day, e1.slot_id
    day2, slot2 = e2.day, e2.slot_id

    # Check e1 at new position ignoring both entries
    ok1, msg1 = validate_cell_edit(e1.id, day2, slot2, e1.class_id, e1.batch_id, e1.teacher_id, e1.room_id, ignore_ids=[e1.id, e2.id])
    # Check e2 at new position ignoring both entries
    ok2, msg2 = validate_cell_edit(e2.id, day1, slot1, e2.class_id, e2.batch_id, e2.teacher_id, e2.room_id, ignore_ids=[e1.id, e2.id])

    if not ok1:
        return False, f"Cannot swap: {msg1}"
    if not ok2:
        return False, f"Cannot swap: {msg2}"

    e1.day, e1.slot_id = day2, slot2
    e2.day, e2.slot_id = day1, slot1
    db.session.commit()
    return True, "Lectures swapped successfully!"


def move_timetable_entry(entry_id, new_day, new_slot_id):
    """
    Moves an entry to a new day and slot with collision prevention.
    """
    e = TimetableEntry.query.get(entry_id)
    if not e:
        return False, "Entry not found."

    ok, msg = validate_cell_edit(e.id, new_day, new_slot_id, e.class_id, e.batch_id, e.teacher_id, e.room_id)
    if not ok:
        return False, msg

    e.day = new_day
    e.slot_id = new_slot_id
    db.session.commit()
    return True, "Lecture moved successfully!"


def generate_smart_timetable(target_class_id=None, target_day=None):
    """
    Intelligent Constraint-Based Timetable Generator
    
    Distributes teacher workloads evenly across Monday to Saturday:
    - Never dumps all lectures of a teacher on the same day.
    - Limits daily lectures per teacher (max 2-3 per day).
    - Spreads theory subjects across the week (max 1 lecture per subject per day).
    - Consecutive 2-hour practical labs for batches.
    - Zero collisions for teachers, classrooms, and classes.
    """
    # 1. Scope definition
    if target_class_id and target_day:
        TimetableEntry.query.filter_by(class_id=target_class_id, day=target_day).delete()
        classes = [AcademicClass.query.get(target_class_id)]
        days = [target_day]
    elif target_class_id:
        TimetableEntry.query.filter_by(class_id=target_class_id).delete()
        classes = [AcademicClass.query.get(target_class_id)]
        days = DAYS_OF_WEEK
    elif target_day:
        TimetableEntry.query.filter_by(day=target_day).delete()
        classes = AcademicClass.query.all()
        days = [target_day]
    else:
        TimetableEntry.query.delete()
        classes = AcademicClass.query.all()
        days = DAYS_OF_WEEK

    db.session.commit()

    # 2. Query available slots (exclude recess)
    all_slots = TimeSlot.query.filter_by(is_recess=False).order_by(TimeSlot.slot_index).all()
    if not all_slots:
        return False, "No active lecture time slots found."

    # Identify consecutive slot pairs for 2-hour practical labs
    # E.g. slots (3,4)=10:30-12:30, (6,7)=01:00-03:00, (9,10)=03:30-05:30
    lab_pairs = []
    for i in range(len(all_slots) - 1):
        s1 = all_slots[i]
        s2 = all_slots[i + 1]
        if s1.slot_index in [3, 6, 9] and s2.slot_index == s1.slot_index + 1:
            lab_pairs.append((s1, s2))

    # 3. Track busy resources: (day, slot_id)
    existing_entries = TimetableEntry.query.all()
    teacher_busy = {(d, s.id): set() for d in DAYS_OF_WEEK for s in all_slots}
    room_busy = {(d, s.id): set() for d in DAYS_OF_WEEK for s in all_slots}
    class_busy = {(d, s.id, c.id): False for d in DAYS_OF_WEEK for s in all_slots for c in AcademicClass.query.all()}
    
    # Track teacher daily load to strictly enforce even weekly distribution
    # Key: (teacher_id, day) -> count of hours scheduled
    teacher_daily_hours = {}
    # Track subject daily appearance per class to avoid same-day repetition
    # Key: (class_id, subject_id, day) -> count of theory lectures
    class_subject_daily = {}

    for e in existing_entries:
        if e.teacher_id:
            teacher_busy.setdefault((e.day, e.slot_id), set()).add(e.teacher_id)
            teacher_daily_hours[(e.teacher_id, e.day)] = teacher_daily_hours.get((e.teacher_id, e.day), 0) + 1
        if e.room_id and e.room and e.room.name != 'Online':
            room_busy.setdefault((e.day, e.slot_id), set()).add(e.room_id)
        if not e.batch_id:
            class_busy[(e.day, e.slot_id, e.class_id)] = True
        if e.subject_id and e.entry_type == 'Theory':
            class_subject_daily[(e.class_id, e.subject_id, e.day)] = class_subject_daily.get((e.class_id, e.subject_id, e.day), 0) + 1

    # 4. Scheduling Loop by Class
    diagnostics = []

    for cls in classes:
        # Get workload assignments for this class
        assignments = TeacherWorkloadAssignment.query.filter_by(class_id=cls.id).all()
        
        # If no workload assignments, derive from subjects
        items_to_schedule = []
        if assignments:
            for a in assignments:
                t = a.teacher
                s = a.subject
                # Theory requirements
                if a.theory_hours > 0:
                    items_to_schedule.append({
                        'type': 'Theory',
                        'subject': s,
                        'teacher': t,
                        'hours': a.theory_hours,
                        'default_room': s.default_room
                    })
                # Practical requirements (each lab is 2 hours)
                if a.practical_hours > 0:
                    num_sessions = max(1, a.practical_hours // 2)
                    for _ in range(num_sessions):
                        items_to_schedule.append({
                            'type': 'Practical',
                            'subject': s,
                            'teacher': t,
                            'hours': 2,
                            'default_room': s.default_room
                        })
        else:
            subjects = Subject.query.filter_by(class_id=cls.id).all()
            for s in subjects:
                t = s.default_teacher
                hrs = s.weekly_hours or 3
                if s.subject_type == 'Practical':
                    sessions = max(1, hrs // 2)
                    for _ in range(sessions):
                        items_to_schedule.append({
                            'type': 'Practical',
                            'subject': s,
                            'teacher': t,
                            'hours': 2,
                            'default_room': s.default_room
                        })
                else:
                    items_to_schedule.append({
                        'type': s.subject_type or 'Theory',
                        'subject': s,
                        'teacher': t,
                        'hours': hrs,
                        'default_room': s.default_room
                    })

        # Separate into Practicals first, then Theory
        practicals = [it for it in items_to_schedule if it['type'] == 'Practical']
        theories = [it for it in items_to_schedule if it['type'] != 'Practical']

        # ---------------------------------------------------------
        # A. Schedule Practicals (2 consecutive hours)
        # ---------------------------------------------------------
        batches = Batch.query.filter_by(class_id=cls.id).all()
        batch_idx = 0

        for pr in practicals:
            placed = False
            t = pr['teacher']
            s = pr['subject']
            rm = pr['default_room'] or Room.query.filter_by(room_type='Laboratory').first()
            assigned_batch = batches[batch_idx % len(batches)] if batches else None
            batch_idx += 1

            # Find best day and lab slot pair
            # Sort days by least teacher daily load to spread evenly
            sorted_days = sorted(days, key=lambda d: teacher_daily_hours.get((t.id, d), 0) if t else 0)

            for day in sorted_days:
                if placed:
                    break
                # Check teacher day off or availability
                if t and (t.day_off == day or not t.is_available):
                    continue
                # Check teacher daily limit (practicals take 2 hours)
                curr_load = teacher_daily_hours.get((t.id, day), 0) if t else 0
                max_allowed = (t.max_daily_lectures or 3) if t else 4
                if curr_load + 2 > max_allowed:
                    continue

                for (s1, s2) in lab_pairs:
                    k1 = (day, s1.id)
                    k2 = (day, s2.id)

                    # Check collisions
                    if t and (t.id in teacher_busy[k1] or t.id in teacher_busy[k2]):
                        continue
                    if rm and rm.name != 'Online' and (rm.id in room_busy[k1] or rm.id in room_busy[k2]):
                        continue
                    if class_busy.get((day, s1.id, cls.id)) or class_busy.get((day, s2.id, cls.id)):
                        continue

                    # Place 2-hour practical session
                    b_name = assigned_batch.name if assigned_batch else "All"
                    title = f"PR-{b_name}-{s.name[:6]}-{t.code if t else ''} ({rm.name if rm else 'Lab'})"
                    
                    e1 = TimetableEntry(
                        day=day,
                        slot_id=s1.id,
                        class_id=cls.id,
                        batch_id=assigned_batch.id if assigned_batch else None,
                        subject_id=s.id,
                        teacher_id=t.id if t else None,
                        room_id=rm.id if rm else None,
                        entry_type='Practical',
                        custom_title=title,
                        custom_teacher=t.code if t else None,
                        custom_room=rm.name if rm else None,
                        custom_batch=b_name,
                        span_slots=2
                    )
                    db.session.add(e1)

                    if t:
                        teacher_busy[k1].add(t.id)
                        teacher_busy[k2].add(t.id)
                        teacher_daily_hours[(t.id, day)] = curr_load + 2
                    if rm and rm.name != 'Online':
                        room_busy[k1].add(rm.id)
                        room_busy[k2].add(rm.id)

                    placed = True
                    break

            if not placed:
                diagnostics.append(f"Practical '{s.code}' ({t.code if t else 'Faculty'}) for {cls.name} could not find free 2-hour lab slot.")

        # ---------------------------------------------------------
        # B. Schedule Theory Lectures (Intelligently Distributed)
        # ---------------------------------------------------------
        for th in theories:
            remaining_hours = th['hours']
            t = th['teacher']
            s = th['subject']
            rm = th['default_room'] or Room.query.filter_by(room_type='Classroom').first()

            # Rule: Distribute hours across DIFFERENT days of the week!
            # E.g. If 3 hours -> 3 distinct days!
            # Sort days based on:
            # 1. Subject NOT already taught on that day (strictly 0 appearances first).
            # 2. Teacher daily workload is lowest on that day.
            # 3. Class already has free slot on that day.
            day_cycle = list(days)
            # Shuffle or cycle to avoid Monday bias
            day_cycle_offset = (cls.id * 2) % len(day_cycle)
            day_cycle = day_cycle[day_cycle_offset:] + day_cycle[:day_cycle_offset]

            for day in day_cycle:
                if remaining_hours <= 0:
                    break

                # RULE: Never assign same theory subject twice on the same day for a class!
                if class_subject_daily.get((cls.id, s.id, day), 0) >= 1:
                    continue

                # RULE: Teacher availability and day off
                if t and (t.day_off == day or not t.is_available):
                    continue

                # RULE: Strict daily workload distribution for teacher
                curr_load = teacher_daily_hours.get((t.id, day), 0) if t else 0
                max_allowed = (t.max_daily_lectures or 3) if t else 4
                if curr_load >= max_allowed:
                    continue

                # Find best slot on this day
                slot_placed = False
                for slot in all_slots:
                    k = (day, slot.id)
                    ck = (day, slot.id, cls.id)

                    # Collision checks
                    if class_busy.get(ck):
                        continue
                    if t and t.id in teacher_busy[k]:
                        continue
                    if rm and rm.name != 'Online' and rm.id in room_busy[k]:
                        continue

                    # Place lecture
                    title = f"TH-{s.code}-{t.code if t else ''} ({rm.name if rm else 'F-12'})"
                    entry = TimetableEntry(
                        day=day,
                        slot_id=slot.id,
                        class_id=cls.id,
                        subject_id=s.id,
                        teacher_id=t.id if t else None,
                        room_id=rm.id if rm else None,
                        entry_type='Theory',
                        custom_title=title,
                        custom_teacher=t.code if t else None,
                        custom_room=rm.name if rm else None,
                        custom_batch="All",
                        span_slots=1
                    )
                    db.session.add(entry)

                    class_busy[ck] = True
                    if t:
                        teacher_busy[k].add(t.id)
                        teacher_daily_hours[(t.id, day)] = curr_load + 1
                    if rm and rm.name != 'Online':
                        room_busy[k].add(rm.id)

                    class_subject_daily[(cls.id, s.id, day)] = 1
                    remaining_hours -= 1
                    slot_placed = True
                    break

            if remaining_hours > 0:
                diagnostics.append(f"Subject '{s.code}' ({t.code if t else 'Faculty'}) for {cls.name} has {remaining_hours} unscheduled hour(s) due to daily limits.")

    db.session.commit()
    
    if diagnostics:
        return True, "Generated with notices:\n" + "\n".join(diagnostics[:5])
    return True, "Smart Timetable generated successfully with balanced weekly workload distribution!"
