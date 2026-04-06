/**
 * SmartStock Landing — Auth Check & Dynamic Buttons
 * Проверяет, авторизован ли пользователь, и меняет поведение кнопок.
 */
(async function () {
  const LOGIN_URL = '/login';
  const DASHBOARD_URL = '/dashboard';
  const PROFILE_URL = '/profile';

  let isAuthenticated = false;

  try {
    console.log('[Landing] Checking auth at /auth/me...');
    const res = await fetch('/auth/me', { credentials: 'include' });
    console.log('[Landing] Auth response status:', res.status);
    if (res.ok) {
      isAuthenticated = true;
      console.log('[Landing] User is authenticated');
    } else {
      console.log('[Landing] User is NOT authenticated (status:', res.status, ')');
    }
  } catch (err) {
    console.log('[Landing] Auth check failed:', err);
    isAuthenticated = false;
  }

  console.log('[Landing] isAuthenticated =', isAuthenticated);

  // --- Nav button "Начать работу" ---
  const navCta = document.querySelector('.nav-links .btn-nav');
  if (navCta) {
    if (isAuthenticated) {
      navCta.textContent = 'Перейти в дашборд';
      navCta.href = DASHBOARD_URL;
    }
  }

  // --- Hero CTA "Попробовать бесплатно" ---
  const heroCta = document.querySelector('.hero-actions .btn-primary');
  if (heroCta) {
    if (isAuthenticated) {
      heroCta.textContent = 'Перейти в дашборд';
      heroCta.href = DASHBOARD_URL;
    }
  }

  // --- Pricing buttons ---
  const pricingButtons = document.querySelectorAll('.pricing-card .btn, .pricing-card .plan-note');
  pricingButtons.forEach((btn) => {
    if (isAuthenticated) {
      // Для авторизованных — ведём в профиль (смена тарифа)
      if (btn.tagName === 'A') {
        btn.href = PROFILE_URL;
      } else if (btn.classList.contains('plan-note')) {
        // "Ваш текущий план" → ссылка на профиль
        const link = document.createElement('a');
        link.href = PROFILE_URL;
        link.className = 'plan-note';
        link.textContent = btn.textContent;
        btn.replaceWith(link);
      }
    } else {
      // Для неавторизованных — ведём на логин
      if (btn.tagName === 'A') {
        btn.href = LOGIN_URL;
      } else if (btn.classList.contains('plan-note')) {
        const link = document.createElement('a');
        link.href = LOGIN_URL;
        link.className = 'plan-note';
        link.textContent = 'Начать бесплатно';
        btn.replaceWith(link);
      }
    }
  });

  // --- CTA section button ---
  const ctaBtn = document.querySelector('.cta-section .btn-primary');
  if (ctaBtn) {
    if (isAuthenticated) {
      ctaBtn.textContent = 'Перейти в дашборд';
      ctaBtn.href = DASHBOARD_URL;
    }
  }
})();
