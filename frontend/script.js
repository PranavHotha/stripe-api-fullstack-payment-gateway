document.addEventListener('DOMContentLoaded', function () {

    let stripe = null;
    let elements = null;
    let cardElement = null;

    // Use absolute backend URL if running frontend on port 5500, otherwise relative
    const API_BASE = (window.location.port === '5500') ? 'http://127.0.0.1:8001' : '';

    // DOM Elements
    const amountInput = document.getElementById('custom-amount');
    const displayAmount = document.getElementById('display-amount');
    const btnText = document.getElementById('btn-text');

    const form = document.getElementById('payment-form');
    const submitBtn = document.getElementById('submit-btn');
    const spinner = document.getElementById('spinner');
    const resultBox = document.getElementById('payment-result');

    // --- Card Element Style ---
    const cardStyle = {
        base: {
            color: '#0f172a',
            fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
            fontSmoothing: 'antialiased',
            fontSize: '15px',
            '::placeholder': { color: '#94a3b8' }
        },
        invalid: {
            color: '#dc2626',
            iconColor: '#dc2626'
        }
    };

    // --- Setup Stripe Card Element ---
    function setupStripeElement(pubKey) {
        const cardContainer = document.getElementById('card-element');

        try {
            if (cardElement) {
                try { cardElement.unmount(); } catch (e) {}
                cardElement = null;
            }

            stripe = Stripe(pubKey);
            elements = stripe.elements();
            cardElement = elements.create('card', {
                style: cardStyle,
                hidePostalCode: true
            });

            cardContainer.innerHTML = '';
            cardElement.mount('#card-element');

            cardElement.on('change', function (event) {
                const displayError = document.getElementById('card-errors');
                displayError.textContent = event.error ? event.error.message : '';
            });

            return true;
        } catch (err) {
            cardContainer.innerHTML = '<p class="card-placeholder-err">⚠️ Failed to initialize Stripe Elements: ' + err.message + '</p>';
            return false;
        }
    }

    // --- Fetch Stripe Publishable Key from backend (.env) ---
    async function loadConfig() {
        const cardContainer = document.getElementById('card-element');
        try {
            const res = await fetch(API_BASE + '/config/');
            if (!res.ok) throw new Error('Backend returned status ' + res.status);
            const data = await res.json();

            if (!data.publishableKey) {
                showResult('STRIPE_PUBLISHABLE_KEY is not configured in backend/.env.', 'error');
                cardContainer.innerHTML = '<p class="card-placeholder-err">⚠️ Stripe keys not configured in backend .env</p>';
                submitBtn.disabled = true;
                return;
            }

            setupStripeElement(data.publishableKey);

        } catch (e) {
            showResult('Could not connect to backend API (http://127.0.0.1:8001). Please ensure the backend server is running.', 'error');
            cardContainer.innerHTML = '<p class="card-placeholder-err">⚠️ Backend connection offline. Start the server to load Stripe.</p>';
            submitBtn.disabled = true;
        }
    }

    // --- Live price update ---
    amountInput.addEventListener('input', function () {
        const val = parseFloat(amountInput.value) || 0;
        const formatted = val.toFixed(2);
        displayAmount.textContent = formatted;
        btnText.textContent = 'Pay $' + formatted;
    });

    // --- Payment Form Submit ---
    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        setLoading(true);
        resultBox.classList.add('hidden');

        const email = document.getElementById('email').value.trim();
        const userAmount = parseFloat(amountInput.value) || 0;

        if (userAmount < 0.50) {
            showResult('Minimum payment amount is $0.50 USD.', 'error');
            setLoading(false);
            return;
        }

        const amountInCents = Math.round(userAmount * 100);
        const payload = { amount: amountInCents, email: email };

        try {
            const response = await fetch(API_BASE + '/create-payment-intent/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                showResult('Payment Error: ' + (data.error || 'Server error occurred'), 'error');
                setLoading(false);
                return;
            }

            if (!stripe || !cardElement) {
                showResult('Stripe is not initialized. Please verify your backend configuration.', 'error');
                setLoading(false);
                return;
            }

            const result = await stripe.confirmCardPayment(data.clientSecret, {
                payment_method: {
                    card: cardElement,
                    billing_details: { email: email }
                }
            });

            if (result.error) {
                // Immediately notify backend that the payment was declined
                const paymentIntentId = (result.error.payment_intent && result.error.payment_intent.id) ||
                                        (data.clientSecret ? data.clientSecret.split('_secret')[0] : null);
                if (paymentIntentId) {
                    try {
                        await fetch(API_BASE + '/confirm-payment/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                paymentIntentId: paymentIntentId,
                                status: 'declined'
                            })
                        });
                    } catch (err) {
                        console.warn('Backend payment decline notification warning:', err);
                    }
                }

                showResult('Payment Declined: ' + result.error.message, 'error');
                setLoading(false);
            } else if (result.paymentIntent && result.paymentIntent.status === 'succeeded') {
                // Immediately notify backend to verify with Stripe and update Transaction status to 'succeeded'
                try {
                    await fetch(API_BASE + '/confirm-payment/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ paymentIntentId: result.paymentIntent.id })
                    });
                } catch (confirmErr) {
                    console.warn('Backend payment confirmation request warning:', confirmErr);
                }

                const txId = data.transactionId || data.orderId;
                window.location.href = 'success.html?transaction_id=' + txId +
                    '&order_id=' + txId +
                    '&payment_id=' + result.paymentIntent.id +
                    '&amount=' + userAmount.toFixed(2);
            }
        } catch (err) {
            showResult('Network Error: ' + err.message, 'error');
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        submitBtn.disabled = isLoading;
        btnText.classList.toggle('hidden', isLoading);
        spinner.classList.toggle('hidden', !isLoading);
    }

    function showResult(message, statusClass) {
        resultBox.innerHTML = message;
        resultBox.className = 'result-box ' + statusClass;
        resultBox.classList.remove('hidden');
    }

    // Initialize
    loadConfig();
});
