(() => {
    const banner = document.getElementById('privacyBanner');
    const settingsButton = document.getElementById('privacySettings');
    const errorMessage = document.getElementById('privacyError');
    const statusMessage = document.getElementById('privacyStatus');
    const nameInput = document.getElementById('privacyName');
    if (!banner || !settingsButton || !errorMessage || !statusMessage || !nameInput) {
        return;
    }

    async function savePrivacyChoice(consent, location = {}) {
        errorMessage.hidden = true;
        statusMessage.hidden = true;
        try {
            const response = await fetch('/api/privacy/consent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    consent,
                    name: consent ? nameInput.value.trim() : '',
                    ...location
                })
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || `Privacy settings could not be saved (${response.status}).`);
            }
            banner.hidden = true;
            settingsButton.hidden = false;
            nameInput.value = '';
            if (consent) {
                await notifyVisit();
            }
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.hidden = false;
        }
    }

    async function notifyVisit() {
        try {
            const response = await fetch('/api/privacy/visit', { method: 'POST' });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || `Visitor notification failed (${response.status}).`);
            }
        } catch (error) {
            statusMessage.textContent = error.message;
            statusMessage.hidden = false;
        }
    }

    function choosePrivacy(consent) {
        if (!consent || !navigator.geolocation) {
            savePrivacyChoice(consent);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => savePrivacyChoice(consent, {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
            }),
            () => savePrivacyChoice(consent),
            { maximumAge: 0, timeout: 10000 }
        );
    }

    banner.querySelectorAll('[data-privacy-consent]').forEach((button) => {
        button.addEventListener('click', () => {
            choosePrivacy(button.dataset.privacyConsent === 'true');
        });
    });

    settingsButton.addEventListener('click', () => {
        banner.hidden = false;
        settingsButton.hidden = true;
    });

    fetch('/api/privacy/consent')
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Privacy settings could not be loaded (${response.status}).`);
            }
            return response.json();
        })
        .then((preference) => {
            banner.hidden = preference.consent === true;
            settingsButton.hidden = !preference.consent;
            if (preference.consent) {
                notifyVisit();
            }
        })
        .catch((error) => {
            banner.hidden = false;
            settingsButton.hidden = true;
            errorMessage.textContent = error.message;
            errorMessage.hidden = false;
        });
})();
