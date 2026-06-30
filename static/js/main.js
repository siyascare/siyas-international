/* ========================================
   SIYA'S INTERNATIONAL - MAIN JS
   ======================================== */

// ===== UTILITY =====
function initFlashMessages() {
    setTimeout(function () {
        document.querySelectorAll('.flash-message').forEach(function (msg) {
            msg.style.transition = 'all 0.3s ease';
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100%)';
            setTimeout(function () { msg.remove(); }, 300);
        });
    }, 5000);
}

function validateName(name) {
    if (!name || name.length < 2) return 'Please enter a valid name';
    if (!/^[A-Za-z\s]+$/.test(name)) return 'Name should contain only letters';
    return null;
}

function validateContact(contact) {
    if (!/^\d{10}$/.test(contact)) return 'Please enter a valid 10-digit number';
    return null;
}

// ===== BOOKING PAGE =====
function initBookingPage() {
    const form = document.getElementById('bookingForm');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        const name    = document.getElementById('fullname').value.trim();
        const contact = document.getElementById('contact').value.trim();
        const brand   = document.getElementById('brand').value;
        const issue   = document.getElementById('issue').value.trim();
        const nameErr = validateName(name);
        const conErr  = validateContact(contact);
        if (nameErr)  { alert(nameErr);  e.preventDefault(); return; }
        if (conErr)   { alert(conErr);   e.preventDefault(); return; }
        if (!brand)   { alert('Please select a brand');       e.preventDefault(); return; }
        if (!issue)   { alert('Please describe your issue');  e.preventDefault(); return; }
    });
}

// ===== CHALAN PAGE =====
function initChalanPage() {
    // Set today's date
    const dateField = document.getElementById('currentDate');
    if (dateField) {
        const t = new Date();
        dateField.value = `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')}`;
    }

    // Photo preview
    const photoInput = document.getElementById('device_photo');
    if (photoInput) {
        photoInput.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;
            if (file.size > 5 * 1024 * 1024) {
                alert('Photo size must be under 5MB');
                this.value = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = function (e) {
                document.getElementById('preview-img').src = e.target.result;
                document.getElementById('photo-preview').style.display = 'block';
            };
            reader.readAsDataURL(file);
        });
    }

    // Form validation
    const form = document.getElementById('chalanForm');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        const name    = document.getElementById('name').value.trim();
        const contact = document.getElementById('contact').value.trim();
        const product = document.getElementById('product').value;
        const brand   = document.getElementById('brand').value;
        const model   = document.getElementById('model').value.trim();
        const body    = document.getElementById('body_damage').value.trim();
        const problem = document.getElementById('problem').value.trim();
        const tray    = document.getElementById('tray_no').value.trim();
        const nameErr = validateName(name);
        const conErr  = validateContact(contact);
        if (nameErr)  { alert(nameErr);                          e.preventDefault(); return; }
        if (conErr)   { alert(conErr);                           e.preventDefault(); return; }
        if (!product) { alert('Please select product type');     e.preventDefault(); return; }
        if (!brand)   { alert('Please select brand');            e.preventDefault(); return; }
        if (!model)   { alert('Please enter model number');      e.preventDefault(); return; }
        if (!body)    { alert('Please describe body condition'); e.preventDefault(); return; }
        if (!problem) { alert('Please describe the problem');    e.preventDefault(); return; }
    });
}

// Auto-fill customer
function fetchCustomer() {
    const contact = document.getElementById('contact').value.trim();
    if (contact.length < 10) return;
    fetch(`/get-customer?contact=${contact}`)
        .then(res => res.json())
        .then(data => {
            if (!data.found) return;
            if (data.name)  { document.getElementById('name').value  = data.name;  }
            if (data.email) { document.getElementById('email').value = data.email; }
            document.getElementById('name').style.background = '#d1fae5';
            setTimeout(() => { document.getElementById('name').style.background = ''; }, 2000);
        })
        .catch(err => console.error(err));
}

// ===== ADMIN DASHBOARD =====
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
}

function toggleRow(rowId) {
    const row = document.getElementById(rowId);
    if (row) row.classList.toggle('show');
}

function toggleBillForm(recordId) {
    const form = document.getElementById('bill-form-' + recordId);
    if (form) form.style.display = form.style.display === 'none' ? 'block' : 'none';
    const detailRow = document.getElementById('details-' + recordId);
    if (detailRow && !detailRow.classList.contains('show')) detailRow.classList.add('show');
}

function filterTable(tableId, searchText) {
    const table  = document.getElementById(tableId);
    const rows   = table.getElementsByTagName('tr');
    const filter = searchText.toUpperCase();
    for (let i = 1; i < rows.length; i++) {
        if (rows[i].classList.contains('expandable-row')) continue;
        let found = false;
        const cells = rows[i].getElementsByTagName('td');
        for (let j = 0; j < cells.length - 1; j++) {
            if ((cells[j].textContent || cells[j].innerText).toUpperCase().includes(filter)) {
                found = true; break;
            }
        }
        rows[i].style.display = found ? '' : 'none';
        const next = rows[i + 1];
        if (next && next.classList.contains('expandable-row')) next.style.display = found ? '' : 'none';
    }
}

function initBillFormEnterKey() {
    const inputs = document.querySelectorAll('.bill-form input, .bill-form textarea, .bill-form select');
    inputs.forEach((input, index) => {
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const next = inputs[index + 1];
                if (next) next.focus();
            }
        });
    });
}

const itemCountMap = {};
function addBillItem(recordId) {
    if (!itemCountMap[recordId]) itemCountMap[recordId] = 4;
    itemCountMap[recordId]++;
    const n = itemCountMap[recordId];
    document.getElementById('extra-items-' + recordId).insertAdjacentHTML('beforeend', `
        <div class="form-group">
            <label>Item ${n}</label>
            <input type="text" name="item${n}" placeholder="Description">
        </div>
        <div class="form-group">
            <label>Amount Rs.</label>
            <input type="number" name="item${n}_amount" placeholder="0">
        </div>
    `);
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', function () {
    initFlashMessages();
    initBookingPage();
    initChalanPage();
    initBillFormEnterKey();
});