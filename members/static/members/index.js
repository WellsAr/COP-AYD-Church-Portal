// =========================
// INITIALIZE PAGE
// =========================

function initializePage() {

    initializeSearch();

    initializeReportFilters();

    initializeProgressBars();

}

// =========================
// INITIAL PAGE LOAD
// =========================

document.addEventListener('DOMContentLoaded', function() {

    initializePage();
    updateActiveNav(window.location.pathname);
    
    // SPA navigation
    document.addEventListener('click', function(e) {

        const link = e.target.closest('a');

        if (
            link &&
            link.href.startsWith(window.location.origin) &&
            !link.hasAttribute('target') &&
            !link.hasAttribute('download')
        ) {

            e.preventDefault();

            loadPage(e, link.getAttribute('href'));

        }

    });

    // Register form submit
    document.addEventListener('submit', function(e) {

        if (e.target.id === 'registerForm') {

            e.preventDefault();

            let formData = new FormData(e.target);

            const status = document.getElementById('status');

            if (status) {
                status.innerText = "Saving...";
            }

            fetch('/register/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {

                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }

                return response.text();
            })
            .then(html => {

                if (!html) return;

                document.getElementById('content').innerHTML = html;

                initializePage();

            });

        }

    });

    // =========================
    // CLOSE MENUS WHEN CLICKING OUTSIDE
    // =========================

    document.addEventListener('click', function(e) {

        // USER DROPDOWN
        const userDropdown =
            document.querySelector('.app-user-dropdown');

        const dropdownMenu =
            document.getElementById('userDropdown');

        if (
            userDropdown &&
            dropdownMenu &&
            !userDropdown.contains(e.target)
        ) {

            dropdownMenu.classList.remove('open');

        }

        // MOBILE MENU
        const mobileNav =
            document.getElementById('mobileNav');

        const mobileBtn =
            document.querySelector('.mobile-menu-btn');

        if (
            mobileNav &&
            mobileBtn &&
            !mobileNav.contains(e.target) &&
            !mobileBtn.contains(e.target)
        ) {

            mobileNav.classList.remove('open');

        }

    });


});

// =========================
// SEARCH
// =========================

function initializeSearch() {

    const searchInput = document.getElementById('search');

    if (!searchInput) return;

    searchInput.addEventListener('keyup', function() {

        let query = this.value.toLowerCase();

        document.querySelectorAll('.js-member-card').forEach(card => {

            let name = (card.dataset.name || '').toLowerCase();

            let phone = (card.dataset.phone || '').toLowerCase();

            card.style.display =
                (name.includes(query) || phone.includes(query))
                    ? ''
                    : 'none';

        });

    });

}

// =========================
// SPA PAGE RENDER
// =========================

function renderPage(url, addToHistory = true) {

    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {

        // Redirect if logged out
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        return response.text();

    })
    .then(html => {

        if (!html) return;

        document.getElementById('content').innerHTML = html;

        // Add history only on normal navigation
        if (addToHistory) {
            history.pushState({}, '', url);
        }

        initializePage();

        // ACTIVE NAV LINK
        updateActiveNav(url);


        // Close menus after navigation
        const mobileNav = document.getElementById('mobileNav');
        const dropdown = document.getElementById('userDropdown');

        if (mobileNav) {
            mobileNav.classList.remove('open');
        }

        if (dropdown) {
            dropdown.classList.remove('open');
        }

    });

}

// =========================
// NAVIGATION
// =========================

function updateActiveNav(url) {

    // DESKTOP LINKS
    const navLinks = document.querySelectorAll('.app-nav-link');

    // MOBILE LINKS
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');

    // REMOVE ACTIVE
    [...navLinks, ...mobileLinks].forEach(link => {
        link.classList.remove('active');
    });

    // DETECT PAGE
    let activePath = '/';

    if (url.startsWith('/member') || url.startsWith('/members')) {
        activePath = '/members/';
    }
    else if (url.startsWith('/register')) {
        activePath = '/register/';
    }
    else if (url.startsWith('/attendance')) {
        activePath = '/attendance/';
    }
    else if (url.startsWith('/reports')) {
        activePath = '/reports/';
    }

    // ADD ACTIVE CLASS
    [...navLinks, ...mobileLinks].forEach(link => {

        const href = link.getAttribute('href');

        if (href === activePath) {
            link.classList.add('active');
        }

    });

}

function loadPage(event, url) {

    if (event) {
        event.preventDefault();
    }

    renderPage(url, true);

}

// =========================
// BACK/FORWARD
// =========================

window.addEventListener('popstate', function() {

    renderPage(location.pathname, false);

});

// =========================
// CAMERA
// =========================

let stream;

// START CAMERA
function startCamera() {

    const video = document.getElementById('camera');

    navigator.mediaDevices.getUserMedia({ video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 1280 },
        height: { ideal: 720 }
    }})
        .then(s => {

            stream = s;

            video.srcObject = stream;

            video.style.display = 'block';

            toggleButtons({
                start: false,
                capture: true,
                stop: true,
                retake: false
            });

        });

}

// STOP CAMERA
function stopCamera() {

    if (stream) {

        stream.getTracks().forEach(track => track.stop());

    }

    document.getElementById('camera').style.display = 'none';

    toggleButtons({
        start: true,
        capture: false,
        stop: false,
        retake: false
    });

}

// CAPTURE
function capture() {

    const video = document.getElementById('camera');

    const canvas = document.createElement('canvas');

    const preview = document.getElementById('preview');

    const ctx = canvas.getContext('2d');

    const MAX_WIDTH = 400;

    let scale = MAX_WIDTH / video.videoWidth;

    canvas.width = MAX_WIDTH;

    canvas.height = video.videoHeight * scale;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataURL = canvas.toDataURL('image/jpeg', 0.6);

    document.getElementById('captured_image').value = dataURL;

    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }

    preview.src = dataURL;

    preview.style.display = 'block';

    video.style.display = 'none';

    toggleButtons({
        start: false,
        capture: false,
        stop: false,
        retake: true
    });

}

// RETAKE
function retake() {

    document.getElementById('captured_image').value = '';

    document.getElementById('preview').style.display = 'none';

    toggleButtons({
        start: true,
        capture: false,
        stop: false,
        retake: false
    });

}

// BUTTON STATE HELPER
function toggleButtons(state) {

    const startBtn = document.getElementById('startBtn');
    const captureBtn = document.getElementById('captureBtn');
    const stopBtn = document.getElementById('stopBtn');
    const retakeBtn = document.getElementById('retakeBtn');

    if (startBtn) {
        startBtn.style.display = state.start ? 'inline-flex' : 'none';
    }

    if (captureBtn) {
        captureBtn.style.display = state.capture ? 'inline-flex' : 'none';
    }

    if (stopBtn) {
        stopBtn.style.display = state.stop ? 'inline-flex' : 'none';
    }

    if (retakeBtn) {
        retakeBtn.style.display = state.retake ? 'inline-flex' : 'none';
    }

}

// =========================
// ATTENDANCE SECTIONS
// =========================

function showSection(section) {

    document.getElementById('unmarked-section').style.display =
        section === 'unmarked' ? '' : 'none';

    document.getElementById('marked-section').style.display =
        section === 'marked' ? '' : 'none';

    document.getElementById('btn-unmarked')
        .classList.toggle('active', section === 'unmarked');

    document.getElementById('btn-marked')
        .classList.toggle('active', section === 'marked');

}

// MOVE TO MARKED
function markPresent(card) {

    card.classList.add('active');

    card.onclick = () => markAbsent(card);

    document.getElementById('marked-section').appendChild(card);

    
    updateAttendanceCounts();
}

// MOVE TO UNMARKED
function markAbsent(card) {

    card.classList.remove('active');

    card.onclick = () => markPresent(card);

    document.getElementById('unmarked-section').appendChild(card);

    updateAttendanceCounts();
}

// =========================
// SAVE ATTENDANCE
// =========================

function saveAttendance() {

    let selected = [];

    document.querySelectorAll('#marked-section .attendance-member-card')
        .forEach(card => {

            selected.push(card.dataset.id);

        });

    const params = new URLSearchParams();

    selected.forEach(id => {
        params.append('present[]', id);
    });

    console.log(selected)
    fetch('/attendance/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        },
        body: params
    })
    .then(res => res.json())
    .then(data => {
        const status = document.getElementById('status');
        if (status) {
            status.innerText =
                `✅ ${data.present}/${data.total} marked present`;
        }

        // Reveal badges ONLY after save
        document.querySelectorAll(
            '#marked-section .attendance-status'
        ).forEach(badge => {

            badge.classList.remove('hidden');

        });

        document.querySelectorAll(
            '#unmarked-section .attendance-status'
        ).forEach(badge => {

            badge.classList.add('hidden');

        });
    });

}


function updateAttendanceCounts() {

    const marked =
        document.querySelectorAll(
            '#marked-section .attendance-member-card'
        ).length;

    const unmarked =
        document.querySelectorAll(
            '#unmarked-section .attendance-member-card'
        ).length;

    document.getElementById('marked-total').innerText = marked;

    document.getElementById('unmarked-total').innerText = unmarked;

    document.getElementById('marked-count').innerText = `${marked} / ${(marked + unmarked)}`;

}


// =========================
// CSRF
// =========================

function getCSRFToken() {

    const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken'));

    return token ? token.split('=')[1] : '';

}



// =========================
// MOBILE NAVIGATION
// =========================

function toggleMobileMenu() {
    
    const mobileNav = document.getElementById('mobileNav');

    if (!mobileNav) return;

    mobileNav.classList.toggle('open');

}

// =========================
// USER DROPDOWN
// =========================

function toggleUserMenu() {

    const dropdown = document.getElementById('userDropdown');

    if (!dropdown) return;

    dropdown.classList.toggle('open');

}




// =========================
// REPORT
// =========================

function initializeReportFilters() {

    const form = document.getElementById(
        'report-filters-form'
    );

    if (!form) return;

    // PREVENT DUPLICATE LISTENERS
    if (form.dataset.initialized === 'true') return;

    form.dataset.initialized = 'true';

    form.addEventListener(
        'submit',
        async function (e) {

            e.preventDefault();

            const params = new URLSearchParams(
                new FormData(form)
            );

            const response = await fetch(
                `${window.location.pathname}?${params}`,
                {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                }
            );

            const html = await response.text();

            const container = document.getElementById(
                'report-container'
            );

            if (!container) return;

            container.innerHTML = html;

            initializePage();

        }
    );

}

function initializeProgressBars() {

    document.querySelectorAll(
        '.report-progress-fill'
    ).forEach(bar => {

        const width = bar.dataset.width || 0;

        bar.style.width = `${width}%`;

    });

}
