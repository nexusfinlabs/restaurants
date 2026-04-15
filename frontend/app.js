(function () {
  var SLOTS = [
    { label: '12:30 – 14:30', value: '12:30' },
    { label: '14:30 – 16:30', value: '14:30' },
    { label: '18:30 – 20:30', value: '18:30' },
    { label: '20:30 – 22:30', value: '20:30' },
  ];

  /* ── WhatsApp URL helper ── */
  function waUrl(customMessage) {
    var phone = (window.RESTAURANT_WHATSAPP || '').replace(/\D/g, '');
    var msg = customMessage != null ? customMessage : window.RESTAURANT_WHATSAPP_MESSAGE || '';
    var base = 'https://wa.me/' + phone;
    if (msg) base += '?text=' + encodeURIComponent(msg);
    return base;
  }

  function todayISO() {
    var d = new Date();
    return d.getFullYear() + '-' +
      String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');
  }

  function isMondayDateString(iso) {
    if (!iso) return false;
    var parts = iso.split('-');
    var d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10), 12, 0, 0);
    return d.getDay() === 1;
  }

  /* ── WhatsApp & mailto links ── */
  document.querySelectorAll('[data-wa-link]').forEach(function (el) {
    var preset = el.getAttribute('data-wa-message');
    el.href = waUrl(preset);
    el.setAttribute('target', '_blank');
    el.setAttribute('rel', 'noopener noreferrer');
  });

  var contactEmail = window.RESTAURANT_CONTACT_EMAIL || 'alobo@nexusfinlabs.com';
  document.querySelectorAll('[data-mailto-link]').forEach(function (el) {
    var card = el.closest('[data-menu-name]');
    var menuName = card ? card.getAttribute('data-menu-name') : '';
    var subject = 'Consulta menú ' + (menuName || 'degustación');
    var body = 'Hola,\n\nEscribo con una pregunta sobre el menú «' + (menuName || '—') + '».\n\n';
    el.href = 'mailto:' + contactEmail +
      '?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(body);
    el.setAttribute('target', '_blank');
    el.setAttribute('rel', 'noopener noreferrer');
  });

  /* ── Carousel ── */
  function initCarousel(root) {
    var track = root.querySelector('.menu-carousel__track');
    var slides = root.querySelectorAll('.menu-carousel__slide');
    var prev = root.querySelector('.menu-carousel__btn--prev');
    var next = root.querySelector('.menu-carousel__btn--next');
    var dotsWrap = root.querySelector('.menu-carousel__dots');
    var n = slides.length;
    var i = 0;
    if (!track || !n) return;

    function go(index) {
      i = (index + n) % n;
      track.style.transform = 'translateX(-' + i * 100 + '%)';
      if (dotsWrap) {
        dotsWrap.querySelectorAll('.menu-carousel__dot').forEach(function (dot, di) {
          dot.setAttribute('aria-current', di === i ? 'true' : 'false');
        });
      }
    }

    if (dotsWrap) {
      dotsWrap.innerHTML = '';
      for (var d = 0; d < n; d++) {
        (function (di) {
          var dot = document.createElement('button');
          dot.type = 'button';
          dot.className = 'menu-carousel__dot';
          dot.setAttribute('aria-label', 'Foto ' + (di + 1));
          dot.addEventListener('click', function () { go(di); });
          dotsWrap.appendChild(dot);
        })(d);
      }
    }
    go(0);
    if (prev) prev.addEventListener('click', function () { go(i - 1); });
    if (next) next.addEventListener('click', function () { go(i + 1); });
  }

  document.querySelectorAll('[data-carousel]').forEach(initCarousel);

  /* ── Modal ── */
  var modal = document.getElementById('booking-modal');
  if (!modal) return;

  var menuLabel   = document.getElementById('booking-modal-menu');
  var dateInput   = document.getElementById('booking-date');
  var dateError   = document.getElementById('booking-date-error');
  var slotsWrap   = document.getElementById('booking-slots');
  var phoneInput  = document.getElementById('booking-phone');
  var nameInput   = document.getElementById('booking-name');
  var emailInput  = document.getElementById('booking-email');
  var paxSelect   = document.getElementById('booking-pax');
  var phoneError  = document.getElementById('booking-phone-error');
  var summaryEl   = document.getElementById('booking-summary');
  var stripeHint  = document.getElementById('booking-stripe-hint');
  var stripeLink  = document.getElementById('booking-stripe-link');
  var copyBtn     = document.getElementById('booking-copy-summary');
  var waFallback  = document.getElementById('booking-wa-fallback');
  var apiStatus   = document.getElementById('booking-api-status');

  var state = { menuName: '', date: '', slot: null, phone: '', name: '', email: '', pax: 2 };

  function showStep(name) {
    modal.querySelectorAll('.booking-step').forEach(function (step) {
      step.hidden = step.getAttribute('data-step') !== name;
    });
  }

  function openModal(card) {
    state.menuName = card.getAttribute('data-menu-name') || 'Menú';
    menuLabel.textContent = state.menuName;
    state.date = ''; state.slot = null; state.phone = '';
    state.name = ''; state.email = ''; state.pax = 2;
    dateInput.value = '';
    if (phoneInput) phoneInput.value = '';
    if (nameInput) nameInput.value = '';
    if (emailInput) emailInput.value = '';
    if (paxSelect) paxSelect.value = '2';
    dateError.hidden = true;
    phoneError.hidden = true;
    if (apiStatus) apiStatus.hidden = true;
    dateInput.min = todayISO();
    showStep('date');
    modal.hidden = false;
    document.body.classList.add('booking-modal-open');
  }

  function closeModal() {
    modal.hidden = true;
    document.body.classList.remove('booking-modal-open');
  }

  function renderSlots() {
    slotsWrap.innerHTML = '';
    SLOTS.forEach(function (slot) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'slot-btn';
      btn.textContent = slot.label;
      btn.addEventListener('click', function () {
        state.slot = slot;
        slotsWrap.querySelectorAll('.slot-btn').forEach(function (b) { b.classList.remove('is-selected'); });
        btn.classList.add('is-selected');
        showStep('phone');
      });
      slotsWrap.appendChild(btn);
    });
  }

  function buildSummary() {
    return (
      'Menú: ' + state.menuName + '\n' +
      'Fecha: ' + state.date + '\n' +
      'Turno: ' + (state.slot ? state.slot.label : '') + '\n' +
      'Personas: ' + state.pax + '\n' +
      'Nombre: ' + state.name + '\n' +
      'Teléfono: ' + state.phone
    );
  }

  function stripeUrlWithRef() {
    var base = (window.STRIPE_BOOKING_URL || '').trim();
    if (!base) return '';
    var ref = 'NEXUS_LOUNGE|' + state.menuName.replace(/\|/g, '') + '|' + state.date + '|' + (state.slot ? state.slot.value : '') + '|' + state.phone.replace(/\s/g, '');
    var sep = base.indexOf('?') >= 0 ? '&' : '?';
    return base + sep + 'client_reference_id=' + encodeURIComponent(ref);
  }

  /* ── API call to backend → Calendar + Email ── */
  function submitReservationToBackend(stripeUrl) {
    var apiBase = (window.RESTAURANT_API_URL || 'http://localhost:8090').replace(/\/$/, '');
    var slotTime = state.slot ? state.slot.value + ':00' : '20:00:00';

    var payload = {
      name: state.name || 'Web-Anon',
      phone: state.phone,
      email: state.email || null,
      date: state.date,
      time: slotTime,
      party_size: state.pax,
      source: 'web',
      notes: 'Menú: ' + state.menuName,
    };

    fetch(apiBase + '/reservations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data && data.external_ref && apiStatus) {
          apiStatus.textContent = '✓ Reserva registrada · Ref: ' + data.external_ref + ' · Calendario actualizado · Email enviado';
          apiStatus.hidden = false;
        }
        // Now confirm (creates Google Calendar event)
        if (data && data.id) {
          return fetch(apiBase + '/reservations/' + data.id + '/confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
          });
        }
      })
      .catch(function () {
        // Backend unreachable — Stripe + WA fallback still shown
        if (apiStatus) {
          apiStatus.textContent = '⚠ Sin conexión al servidor — usa el enlace Stripe o WhatsApp.';
          apiStatus.style.color = '#f59e0b';
          apiStatus.hidden = false;
        }
      });
  }

  /* ── Modal events ── */
  modal.querySelectorAll('[data-close-modal]').forEach(function (el) {
    el.addEventListener('click', closeModal);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
  });

  document.querySelectorAll('[data-open-booking]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = btn.closest('[data-menu-name]');
      if (card) openModal(card);
    });
  });

  modal.querySelectorAll('[data-goto]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = btn.getAttribute('data-goto');
      if (target === 'slot') {
        var v = dateInput.value;
        if (!v) { dateError.textContent = 'Selecciona una fecha.'; dateError.hidden = false; return; }
        if (isMondayDateString(v)) { dateError.textContent = 'Los lunes cerramos. Elige otro día.'; dateError.hidden = false; return; }
        dateError.hidden = true;
        state.date = v;
        renderSlots();
        showStep('slot');
      } else if (target === 'date') {
        showStep('date');
      } else if (target === 'phone') {
        showStep('phone');
      }
    });
  });

  dateInput.addEventListener('change', function () {
    if (dateInput.value && isMondayDateString(dateInput.value)) {
      dateError.textContent = 'Los lunes cerramos. Elige otro día.';
      dateError.hidden = false;
    } else {
      dateError.hidden = true;
    }
  });

  document.getElementById('booking-phone-next').addEventListener('click', function () {
    var raw = (phoneInput.value || '').trim();
    var digits = raw.replace(/\D/g, '');
    if (digits.length < 9) {
      phoneError.textContent = 'Introduce un teléfono válido (mín. 9 dígitos).';
      phoneError.hidden = false;
      return;
    }
    if (nameInput && !nameInput.value.trim()) {
      phoneError.textContent = 'Introduce tu nombre.';
      phoneError.hidden = false;
      return;
    }
    phoneError.hidden = true;

    state.phone = raw;
    state.name  = nameInput ? nameInput.value.trim() : 'Web';
    state.email = emailInput ? emailInput.value.trim() : '';
    state.pax   = paxSelect ? parseInt(paxSelect.value, 10) : 2;

    var summary = buildSummary();
    summaryEl.textContent = summary;

    var url = stripeUrlWithRef();
    if (url) {
      stripeLink.href = url;
      stripeLink.hidden = false;
      stripeHint.textContent = 'Completa el depósito de garantía en Stripe. El evento ya está en nuestro calendario.';
    } else {
      stripeLink.hidden = true;
      stripeHint.textContent = 'Añade STRIPE_BOOKING_URL en config.js para activar el pago. Usa WhatsApp como alternativa.';
    }

    waFallback.href = waUrl('Reserva solicitada desde la web:\n\n' + summary + '\n\n¿Podéis confirmar?');

    // Fire API call → Google Calendar event + HTML email
    submitReservationToBackend(url);

    showStep('stripe');
  });

  copyBtn.addEventListener('click', function () {
    var text = buildSummary();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        copyBtn.textContent = 'Copiado';
        setTimeout(function () { copyBtn.textContent = 'Copiar resumen'; }, 2000);
      });
    } else {
      window.prompt('Copia el resumen:', text);
    }
  });

  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.nav-main');
  if (toggle && nav) {
    toggle.addEventListener('click', function () { nav.classList.toggle('is-open'); });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('is-open'); });
    });
  }
})();
