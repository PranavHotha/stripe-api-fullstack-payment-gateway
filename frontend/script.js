document.addEventListener('DOMContentLoaded', function () {

    let stripe = null;
    let elements = null;
    let cardElement = null;

    const DEFAULT_PUB_KEY = 'pk_test_51R1SnWDFY4taHmOmRLTblZJEsWaleUW9bUJCXbKQIBWyb34aqHlZRSlLrASPFJ7JWmMBwdleFL4qEIgFs8odXLAu00wH9mMHtR';

    let activePublishableKey = localStorage.getItem('stripe_pub_key') || '';
    let activeSecretKey = localStorage.getItem('stripe_sec_key') || '';

    // DOM Elements
    const pubKeyInput = document.getElementById('publishable-key-input');
    const secKeyInput = document.getElementById('secret-key-input');
    const saveKeysBtn = document.getElementById('save-keys-btn');
    const clearKeysBtn = document.getElementById('clear-keys-btn');
    const keysMsg = document.getElementById('keys-msg');

    const keyToggleBtn = document.getElementById('key-toggle-btn');
    const keySettingsPanel = document.getElementById('key-settings-panel');
    const closePanelBtn = document.getElementById('close-panel-btn');
    const keyStatusDot = document.getElementById('key-status-dot');

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

    // --- Toggle Panel ---
    keyToggleBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        keySettingsPanel.classList.toggle('hidden');
    });

    closePanelBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        keySettingsPanel.classList.add('hidden');
    });

    // --- Save Keys ---
    saveKeysBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        const pubVal = pubKeyInput.value.trim();
        const secVal = secKeyInput.value.trim();

        if (pubVal) {
            localStorage.setItem('stripe_pub_key', pubVal);
            activePublishableKey = pubVal;
        } else {
            localStorage.removeItem('stripe_pub_key');
            activePublishableKey = '';
        }

        if (secVal) {
            localStorage.setItem('stripe_sec_key', secVal);
            activeSecretKey = secVal;
        } else {
            localStorage.removeItem('stripe_sec_key');
            activeSecretKey = '';
        }

        const effectivePub = activePublishableKey || DEFAULT_PUB_KEY;
        const isOk = setupStripeElement(effectivePub);
        updateStatusDot(effectivePub, Boolean(activeSecretKey || secVal));

        showKeysMsg(isOk ? 'API Keys saved successfully!' : 'Keys saved, but Publishable Key may be invalid.', isOk ? 'success' : 'error');

        setTimeout(function () {
            keysMsg.classList.add('hidden');
            if (isOk) keySettingsPanel.classList.add('hidden');
        }, 1800);
    });

    // --- Clear/Reset Keys ---
    clearKeysBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        localStorage.removeItem('stripe_pub_key');
        localStorage.removeItem('stripe_sec_key');
        activePublishableKey = '';
        activeSecretKey = '';
        pubKeyInput.value = '';
        secKeyInput.value = '';

        setupStripeElement(DEFAULT_PUB_KEY);
        updateStatusDot(DEFAULT_PUB_KEY, false);
        showKeysMsg('Custom keys reset to defaults.', 'success');
        setTimeout(function () { keysMsg.classList.add('hidden'); }, 2000);
    });

    // --- Setup Stripe Card Element ---
    function setupStripeElement(pubKey) {
        const cardContainer = document.getElementById('card-element');
        const keyToUse = pubKey || DEFAULT_PUB_KEY;

        try {
            if (cardElement) {
                try { cardElement.unmount(); } catch (e) {}
                cardElement = null;
            }

            stripe = Stripe(keyToUse);
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
            cardContainer.innerHTML = '<p class="card-placeholder-err">⚠️ Invalid Stripe Key: ' + err.message + '</p>';
            return false;
        }
    }

    // --- Fetch config from backend ---
    async function loadConfig() {
        try {
            const res = await fetch('http://127.0.0.1:8001/config/');
            if (!res.ok) throw new Error('Non-200 response');
            const data = await res.json();

            const backendPubKey = data.publishableKey || '';
            const backendHasSecret = data.hasSecretKey || false;
            const effectivePubKey = activePublishableKey || backendPubKey || DEFAULT_PUB_KEY;

            if (activePublishableKey) {
                pubKeyInput.value = activePublishableKey;
            } else if (backendPubKey) {
                pubKeyInput.placeholder = backendPubKey.substring(0, 20) + '...';
            }

            if (activeSecretKey) {
                secKeyInput.value = activeSecretKey;
            } else if (backendHasSecret) {
                secKeyInput.placeholder = '•••••••••••••••• (Loaded from .env)';
            }

            updateStatusDot(effectivePubKey, activeSecretKey || backendHasSecret);
            setupStripeElement(effectivePubKey);

        } catch (e) {
            // Backend offline — fall back to defaults
            const fallbackKey = activePublishableKey || DEFAULT_PUB_KEY;
            if (activePublishableKey) pubKeyInput.value = activePublishableKey;
            if (activeSecretKey) secKeyInput.value = activeSecretKey;
            setupStripeElement(fallbackKey);
            updateStatusDot(fallbackKey, Boolean(activeSecretKey));
        }
    }

    // --- Status dot ---
    function updateStatusDot(pubKey, hasSecret) {
        if (pubKey && hasSecret) {
            keyStatusDot.className = 'status-dot dot-green';
            keyStatusDot.title = 'Stripe API Keys active';
        } else if (pubKey || hasSecret) {
            keyStatusDot.className = 'status-dot dot-orange';
            keyStatusDot.title = 'Partially configured';
        } else {
            keyStatusDot.className = 'status-dot dot-red';
            keyStatusDot.title = 'API Keys missing — click to configure';
        }
    }

    // --- Keys message helper ---
    function showKeysMsg(text, type) {
        keysMsg.textContent = text;
        keysMsg.className = 'keys-msg ' + type;
        keysMsg.classList.remove('hidden');
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

        const email = document.getElementById('email').value;
        const userAmount = parseFloat(amountInput.value) || 0;

        if (userAmount < 0.50) {
            showResult('Minimum payment amount is $0.50 USD.', 'error');
            setLoading(false);
            return;
        }

        const amountInCents = Math.round(userAmount * 100);

        const payload = { amount: amountInCents, email: email };

        const customSec = secKeyInput.value.trim() || activeSecretKey;
        if (customSec) payload.secretKey = customSec;

        try {
            const response = await fetch('http://127.0.0.1:8001/create-payment-intent/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.error) {
                showResult('Backend Error: ' + data.error, 'error');
                setLoading(false);
                return;
            }

            if (!stripe || !cardElement) {
                showResult('Stripe is not initialized. Please enter a valid Publishable Key.', 'error');
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
                showResult('Payment Failed: ' + result.error.message, 'error');
                setLoading(false);
            } else if (result.paymentIntent.status === 'succeeded') {
                window.location.href = 'success.html?order_id=' + data.orderId +
                    '&payment_id=' + result.paymentIntent.id +
                    '&amount=' + userAmount.toFixed(2);
            }
        } catch (err) {
            showResult('Connection Error: ' + err.message, 'error');
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

    // Boot
    loadConfig();
});
