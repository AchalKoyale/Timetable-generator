/**
 * Editable Timetable Interface Script - MGM COE
 * Features:
 * - Direct cell click editing (Subject, Faculty, Room, Batch, Type, Custom Title)
 * - Moving lectures across days and time slots
 * - Swapping two lectures with collision checking
 * - Instant conflict detection & force save override
 * - Delete period & Reset to original PDF
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
    const modalSwapSection = document.getElementById('modalSwapSection');
    const swapTargetSelect = document.getElementById('swapTargetSelect');
    const btnExecuteSwap = document.getElementById('btnExecuteSwap');

    // Attach click listeners to all timetable cell items
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
        // Reset modal alert state
        conflictAlert.classList.add('d-none');
        conflictText.textContent = '';
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Changes';

        document.getElementById('editEntryId').value = data.entryId || '';
        document.getElementById('editClassId').value = data.classId;

        // Populate Day & Time Slot dropdowns
        const daySelect = document.getElementById('editDay');
        if (daySelect && data.day) {
            daySelect.value = data.day;
        }

        const slotSelect = document.getElementById('editSlotId');
        if (slotSelect && data.slotId) {
            slotSelect.value = data.slotId;
        }

        // Set entity fields
        if (document.getElementById('editSubjectId')) document.getElementById('editSubjectId').value = data.subjectId || '';
        if (document.getElementById('editTeacherId')) document.getElementById('editTeacherId').value = data.teacherId || '';
        if (document.getElementById('editRoomId')) document.getElementById('editRoomId').value = data.roomId || '';
        if (document.getElementById('editBatchId')) document.getElementById('editBatchId').value = data.batchId || '';
        if (document.getElementById('editEntryType')) document.getElementById('editEntryType').value = data.entryType || 'Theory';
        if (document.getElementById('editCustomTitle')) document.getElementById('editCustomTitle').value = data.customTitle || '';

        // Header info
        const dayLabel = document.getElementById('modalDayLabel');
        if (dayLabel) dayLabel.textContent = data.day || 'Schedule Period';
        
        // Delete button & Swap Section visibility
        if (data.entryId) {
            deleteBtn.classList.remove('d-none');
            if (modalSwapSection) {
                modalSwapSection.classList.remove('d-none');
                populateSwapTargets(data.entryId);
            }
        } else {
            deleteBtn.classList.add('d-none');
            if (modalSwapSection) {
                modalSwapSection.classList.add('d-none');
            }
        }

        editModal.show();
    }

    // Populate swap target options with other scheduled periods in the view
    function populateSwapTargets(currentEntryId) {
        if (!swapTargetSelect) return;
        swapTargetSelect.innerHTML = '<option value="">-- Select Lecture to Swap with --</option>';

        const allItems = document.querySelectorAll('.tt-cell-item');
        allItems.forEach(item => {
            const id = item.dataset.entryId;
            if (id && id !== currentEntryId) {
                const day = item.dataset.day;
                const title = item.dataset.customTitle || item.innerText.trim();
                const opt = document.createElement('option');
                opt.value = id;
                opt.textContent = `[${day}] ${title}`;
                swapTargetSelect.appendChild(opt);
            }
        });
    }

    // Execute Swap button
    if (btnExecuteSwap) {
        btnExecuteSwap.addEventListener('click', function () {
            const currentEntryId = document.getElementById('editEntryId').value;
            const targetEntryId = swapTargetSelect ? swapTargetSelect.value : '';

            if (!currentEntryId || !targetEntryId) {
                alert('Please select a target lecture to swap with.');
                return;
            }

            btnExecuteSwap.disabled = true;
            btnExecuteSwap.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Swapping...';

            fetch('/api/timetable/swap', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    entry_id_1: parseInt(currentEntryId),
                    entry_id_2: parseInt(targetEntryId)
                })
            })
            .then(res => res.json().then(data => ({ status: res.status, body: data })))
            .then(({ status, body }) => {
                if (body.success) {
                    editModal.hide();
                    window.location.reload();
                } else {
                    conflictAlert.classList.remove('d-none');
                    conflictText.innerHTML = `<strong>Cannot Swap:</strong> ${body.message}`;
                    btnExecuteSwap.disabled = false;
                    btnExecuteSwap.innerHTML = '<i class="fas fa-random me-1"></i> Swap';
                }
            })
            .catch(err => {
                console.error(err);
                alert('An error occurred while swapping lectures.');
                btnExecuteSwap.disabled = false;
                btnExecuteSwap.innerHTML = '<i class="fas fa-random me-1"></i> Swap';
            });
        });
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
