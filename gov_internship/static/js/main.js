function toggleMobileNav() {
    const nav = document.getElementById('mobileNav');
    if (nav) nav.classList.toggle('open');
}

function animateCounters() {
    document.querySelectorAll('[data-count]').forEach(el => {
        const target = parseInt(el.getAttribute('data-count'), 10);
        if (!target || target === 0) return;
        let current = 0;
        const step = Math.max(1, Math.floor(target / 40));
        const timer = setInterval(() => {
            current = Math.min(current + step, target);
            el.textContent = current;
            if (current >= target) clearInterval(timer);
        }, 30);
    });
}

function animateProgressBars() {
    document.querySelectorAll('.breakdown-fill').forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => { bar.style.width = width; }, 100);
    });
}

function initMatchForm() {
    const form = document.getElementById('matchForm');
    if (!form) return;
    form.addEventListener('submit', () => {
        const btn = document.getElementById('matchBtn');
        if (btn) {
            btn.textContent = '⏳ Analyzing...';
            btn.disabled = true;
        }
    });
}

function initSkillSuggestions() {
    const skillsInput = document.querySelector('textarea[name="skills"], input[name="skills"]');
    if (!skillsInput) return;
    const suggestions = [
        'Python', 'Java', 'C++', 'Machine Learning', 'Data Analysis', 'SQL',
        'TensorFlow', 'PyTorch', 'React', 'Node.js', 'Cloud Computing',
        'MATLAB', 'GIS', 'Remote Sensing', 'Policy Research', 'Economics',
        'Cybersecurity', 'Network Security', 'Embedded Systems', 'FPGA',
        'Excel', 'Power BI', 'Tableau', 'R', 'Statistics', 'Deep Learning',
        'Computer Vision', 'NLP', 'Signal Processing', 'CAD Tools'
    ];

    const container = document.createElement('div');
    container.className = 'skill-suggestions';
    container.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;margin-top:8px;';

    suggestions.slice(0, 12).forEach(skill => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'skill-chip';
        chip.style.cursor = 'pointer';
        chip.textContent = '+ ' + skill;
        chip.addEventListener('click', () => {
            const current = skillsInput.value.trim();
            const skills = current ? current.split(',').map(s => s.trim()).filter(Boolean) : [];
            if (!skills.includes(skill)) {
                skills.push(skill);
                skillsInput.value = skills.join(', ');
            }
        });
        container.appendChild(chip);
    });

    skillsInput.parentElement.appendChild(container);
}

function highlightActiveNavLink() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '/' && path.startsWith(href)) {
            link.classList.add('active');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    animateCounters();
    animateProgressBars();
    initMatchForm();
    initSkillSuggestions();
    highlightActiveNavLink();

    setTimeout(() => {
        document.querySelectorAll('.flash').forEach(f => {
            f.style.transition = 'opacity 0.5s';
            f.style.opacity = '0';
            setTimeout(() => f.remove(), 500);
        });
    }, 5000);

    document.querySelectorAll('.internship-card, .internship-list-card, .result-card').forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(12px)';
        card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, i * 50);
    });
});
