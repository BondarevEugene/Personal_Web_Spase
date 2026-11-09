/* OmniFactory Studio v2 — accessible, dependency-free interaction layer.
 * Visual effects remain progressive enhancements. Lead requests go only to
 * the backend; bot credentials are NEVER stored in browser JavaScript.
 */
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const year = $('#year');
  if (year) year.textContent = String(new Date().getFullYear());

  // Mobile navigation: keep aria-expanded in sync, and close after selecting a link.
  const toggle = $('#menu-toggle');
  const nav = $('#main-nav');
  const closeNav = () => {
    nav?.classList.remove('open');
    toggle?.setAttribute('aria-expanded', 'false');
    toggle?.setAttribute('aria-label', 'Открыть меню');
  };
  toggle?.addEventListener('click', () => {
    const isOpen = nav?.classList.toggle('open') ?? false;
    toggle.setAttribute('aria-expanded', String(isOpen));
    toggle.setAttribute('aria-label', isOpen ? 'Закрыть меню' : 'Открыть меню');
  });
  nav?.querySelectorAll('a').forEach(a => a.addEventListener('click', closeNav));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeNav();
  });
  document.addEventListener('click', event => {
    if (!nav?.contains(event.target) && !toggle?.contains(event.target)) closeNav();
  });

  // Repeated scroll computations are limited to one animation frame.
  const progress = $('#scroll-progress');
  const header = $('#site-header');
  const backTop = $('#back-top');
  let rafPending = false;
  const updateScroll = () => {
    rafPending = false;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.width = `${max > 0 ? window.scrollY / max * 100 : 0}%`;
    header?.classList.toggle('scrolled', window.scrollY > 15);
    backTop?.classList.toggle('show', window.scrollY > 700);
  };
  window.addEventListener('scroll', () => {
    if (!rafPending) {
      rafPending = true;
      requestAnimationFrame(updateScroll);
    }
  }, {passive: true});
  updateScroll();
  backTop?.addEventListener('click', () => {
    window.scrollTo({top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  });

  // Content must never remain hidden on browsers without IntersectionObserver.
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!('IntersectionObserver' in window) || reduceMotion) {
    $$('.reveal').forEach(el => el.classList.add('visible'));
  } else {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(({target, isIntersecting}) => {
        if (!isIntersecting) return;
        target.classList.add('visible');
        observer.unobserve(target);
      });
    }, {threshold: 0.06, rootMargin: '0px 0px 45px 0px'});
    $$('.reveal').forEach(el => observer.observe(el));
  }

  // Highlight active navigation sections without modifying URL or browser history.
  if ('IntersectionObserver' in window) {
    const links = $$('#main-nav a[href^="#"]');
    const ids = new Set(links.map(a => a.getAttribute('href')?.slice(1)));
    const sections = $$('section[id]').filter(section => ids.has(section.id));
    const sectionObserver = new IntersectionObserver(entries => {
      entries.forEach(({target, isIntersecting}) => {
        if (!isIntersecting) return;
        links.forEach(link => link.classList.toggle('active', link.getAttribute('href') === `#${target.id}`));
      });
    }, {rootMargin: '-30% 0px -58% 0px'});
    sections.forEach(el => sectionObserver.observe(el));
  }

  // Telegram lead submission. No client-side token or chat_id: secrets stay on server.
  const leadForm = $('#lead-form');
  const status = $('#lead-status');
  const submit = leadForm?.querySelector('button[type="submit"]');
  const setStatus = (message, kind = '') => {
    if (!status) return;
    status.textContent = message;
    status.className = `form-status ${kind}`.trim();
  };
  leadForm?.addEventListener('submit', async event => {
    event.preventDefault();
    if (!leadForm.reportValidity() || !submit) return;
    const formData = new FormData(leadForm);
    const data = Object.fromEntries(formData.entries());
    if (data.website) return;  // Honeypot, do not alert bots.
    submit.disabled = true;
    setStatus('Отправляем заявку…');
    try {
      const response = await fetch('/studio/api/lead', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: data.name, contact: data.contact, topic: data.topic, message: data.message, website: data.website}),
      });
      let payload = {};
      try { payload = await response.json(); } catch (_) { /* Generic server/network error below. */ }
      if (!response.ok) {
        if (response.status === 503 || response.status === 404) {
          throw new Error('Приём заявок в Telegram пока не подключён. Для связи используй GitHub в разделе контактов.');
        }
        if (response.status === 429) throw new Error('Слишком много запросов. Повтори попытку позже.');
        throw new Error(response.status === 422 ? 'Проверь данные в форме.' : 'Не удалось отправить заявку. Попробуй позже.');
      }
      if (payload.ok !== true) throw new Error('Не получили подтверждение доставки. Попробуй позже.');
      setStatus('Заявка отправлена! Сообщение доставлено в Telegram студии.', 'success');
      leadForm.reset();
    } catch (error) {
      setStatus(error?.message || 'Ошибка сети. Повтори попытку позже.', 'error');
    } finally {
      submit.disabled = false;
    }
  });


  // Portfolio filters are display-only: no network calls or claims about product status.
  const filterButtons = $$('.case-filterbar button[data-filter]');
  const caseCards = $$('.project-list .case');
  filterButtons.forEach(button => button.addEventListener('click', () => {
    const category = button.dataset.filter;
    filterButtons.forEach(other => {
      const selected = other === button;
      other.classList.toggle('active', selected);
      other.setAttribute('aria-pressed', String(selected));
    });
    caseCards.forEach(card => {
      card.hidden = category !== 'all' && !(card.dataset.category || '').split(/\s+/).includes(category);
    });
  }));

  // Service/package CTAs prefill the real lead form. The visitor can edit freely.
  $$('[data-brief-topic]').forEach(button => button.addEventListener('click', () => {
    const topic = leadForm?.querySelector('select[name="topic"]');
    const message = leadForm?.querySelector('textarea[name="message"]');
    if (topic) topic.value = button.dataset.briefTopic || '';
    if (message && !message.value.trim()) message.value = button.dataset.briefText || '';
    $('#contact')?.scrollIntoView({behavior: reduceMotion ? 'auto' : 'smooth', block: 'start'});
    // Focus after click for keyboard users without clobbering typed text.
    if (!reduceMotion) setTimeout(() => leadForm?.querySelector('input[name="name"]')?.focus({preventScroll:true}), 500);
  }));

  // Keep only one FAQ entry expanded for easier scanning on mobile.
  const faqs = $$('.faq-list details');
  faqs.forEach(detail => detail.addEventListener('toggle', () => {
    if (detail.open) faqs.forEach(other => { if (other !== detail) other.open = false; });
  }));

})();
