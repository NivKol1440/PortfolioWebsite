(() => {
    const loadingScreen = document.getElementById('loadingScreen');
    if (!loadingScreen) {
        return;
    }

    const minimumDisplayTime = 500;
    const fallbackDisplayTime = 8000;
    const startedAt = performance.now();
    let dismissed = false;

    function dismissLoadingScreen() {
        if (dismissed) {
            return;
        }
        dismissed = true;
        window.clearTimeout(fallbackTimer);

        const remainingTime = Math.max(0, minimumDisplayTime - (performance.now() - startedAt));
        window.setTimeout(() => {
            loadingScreen.classList.add('is-hidden');
            loadingScreen.setAttribute('aria-hidden', 'true');
        }, remainingTime);
    }

    const fallbackTimer = window.setTimeout(dismissLoadingScreen, fallbackDisplayTime);

    if (document.readyState === 'complete') {
        dismissLoadingScreen();
    } else {
        window.addEventListener('load', dismissLoadingScreen, { once: true });
    }
})();
