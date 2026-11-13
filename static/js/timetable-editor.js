/**
 * Editable Timetable Interface Script
 * Allows clicking any period cell to view/edit:
 * - Subject
 * - Faculty
 * - Room / Laboratory
 * - Class / Batch
 * - Start & End time
 * - Lecture / Practical / Meeting
 * Provides Live Conflict Checking, Save Changes, Delete and Reset
 */

document.addEventListener('DOMContentLoaded', function () {
    const editModalEl = document.getElementById('cellEditModal');
    if (!editModalEl) return;

    const editModal = new bootstrap.Modal(editModalEl);
    const form = document.getElementById('cellEditForm');
    const conflictAlert = document.getElementById('modalConflictAlert');
    const conflictText = document.getElementById('modalConflictText');
    const deleteBtn = document.getElementById('modalDeleteBtn');
    const saveBtn = document.getElementById('modalSaveBtn');

    // Attach click listeners to all timetable items
    document.querySelectorAll('.tt-cell-item').forEach(item => {
        item.addEventListener('click', function (e) {
            e.stopPropagation();
            openEditor({
                entryId: this.dataset.entryId,
                day: this.dataset.day,
                slotId: this.dataset.slotId,
                classId: this.dataset.classId,
                batchId: this.dataset.batchId,
                subjectId: this.dataset.subjectId,
                teacherId: this.dataset.teacherId,
                roomId: this.dataset.roomId,
                entryType: this.dataset.entryType || 'Theory',
                customTitle: this.dataset.customTitle || ''
            });
        });
    });

    // Attach click listeners to empty slot buttons
    document.querySelectorAll('.empty-slot-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            openEditor({
                entryId: '',
                day: this.dataset.day,
                slotId: this.dataset.slotId,
                classId: this.dataset.classId,
                batchId: '',
                subjectId: '',
                teacherId: '',
                roomId: '',
                entryType: 'Theory',
                customTitle: ''
            });
        });
    });

    function openEditor(data) {
        // Reset modal state
        conflictAlert.classList.add('d-none');
        conflictText.textContent = '';
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Changes';

        document.getElementById('editEntryId').value = data.entryId || '';
        document.getElementById('editDay').value = data.day;
        document.getElementById('editSlotId').value = data.slotId;
        document.getElementById('editClassId').value = data.classId;

        // Set form fields
        if (document.getElementById('editSubjectId')) document.getElementById('editSubjectId').value = data.subjectId || '';
        if (document.getElementById('editTeacherId')) document.getElementById('editTeacherId').value = data.teacherId || '';
        if (document.getElementById('editRoomId')) document.getElementById('editRoomId').value = data.roomId || '';
        if (document.getElementById('editBatchId')) document.getElementById('editBatchId').value = data.batchId || '';
        if (document.getElementById('editEntryType')) document.getElementById('editEntryType').value = data.entryType || 'Theory';
        if (document.getElementById('editCustomTitle')) document.getElementById('editCustomTitle').value = data.customTitle || '';

        // Header info
        const dayLabel = document.getElementById('modalDayLabel');
        const slotLabel = document.getElementById('modalSlotLabel');
        if (dayLabel) dayLabel.textContent = data.day;
        
        // Delete button visibility
        if (data.entryId) {
            deleteBtn.classList.remove('d-none');
        } else {
            deleteBtn.classList.add('d-none');
        }

        editModal.show();
    }

    // Handle Save Form Submission
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        saveCell(false);
    });

    function saveCell(forceSave = false) {
        const payload = {
            entry_id: document.getElementById('editEntryId').value || null,
            day: document.getElementById('editDay').value,
            slot_id: parseInt(document.getElementById('editSlotId').value),
            class_id: parseInt(document.getElementById('editClassId').value),
            batch_id: document.getElementById('editBatchId').value ? parseInt(document.getElementById('editBatchId').value) : null,
            subject_id: document.getElementById('editSubjectId').value ? parseInt(document.getElementById('editSubjectId').value) : null,
            teacher_id: document.getElementById('editTeacherId').value ? parseInt(document.getElementById('editTeacherId').value) : null,
            room_id: document.getElementById('editRoomId').value ? parseInt(document.getElementById('editRoomId').value) : null,
            entry_type: document.getElementById('editEntryType').value,
            custom_title: document.getElementById('editCustomTitle').value,
            force_save: forceSave
        };

        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

        fetch('/api/timetable/entry', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(res => res.json().then(data => ({ status: res.status, body: data })))
        .then(({ status, body }) => {
            if (body.success) {
                editModal.hide();
                window.location.reload();
            } else if (body.has_conflict) {
                // Show clash warning
                conflictAlert.classList.remove('d-none');
                conflictText.innerHTML = `<strong>Conflict Detected:</strong> ${body.message}<br/><button type="button" id="forceSaveBtn" class="btn btn-sm btn-outline-danger mt-2"><i class="fas fa-exclamation-triangle me-1"></i> Force Save Anyway</button>`;
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Changes';

                document.getElementById('forceSaveBtn').addEventListener('click', function () {
                    saveCell(true);
                });
            } else {
                alert('Error: ' + (body.message || 'Could not save entry.'));
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Changes';
            }
        })
        .catch(err => {
            console.error(err);
            alert('A network or server error occurred.');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Changes';
        });
    }

    // Handle Delete Entry
    deleteBtn.addEventListener('click', function () {
        const entryId = document.getElementById('editEntryId').value;
        if (!entryId) return;

        if (confirm('Are you sure you want to delete this period entry?')) {
            deleteBtn.disabled = true;
            fetch(`/api/timetable/entry/${entryId}`, {
                method: 'DELETE'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    editModal.hide();
                    window.location.reload();
                } else {
                    alert('Could not delete: ' + data.message);
                    deleteBtn.disabled = false;
                }
            })
            .catch(err => {
                console.error(err);
                alert('Error deleting entry.');
                deleteBtn.disabled = false;
            });
        }
    });
});
