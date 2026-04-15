(function () {
  var SLOTS = [
    { label: '12:30 – 14:30', value: '12:30-14:30' },
    { label: '14:30 – 16:30', value: '14:30-16:30' },
    { label: '18:30 – 20:30', value: '18:30-20:30' },
    { label: '20:30 – 22:30', value: '20:30-22:30' },
  ];

  function waUrl(customMessage) {
    var phone = (window.RESTAURANT_WHATSAPP || '').replace(/\D/g, '');
    var msg = customMessage != null ? customMessage : window.RESTAURANT_WHATSAPP_MESSAGE || '';
    var base = 'https://wa.me/' + phone;
    if (msg) {
      base += '?text=' + encodeURIComponent(msg);
    }
    return base;
  }

  function todayISO() {
    var d = new Date();
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + day;
  }

  function isMondayDateString(iso) {
    if (!iso) return false;
    var parts = iso.split('-');
    var d = new Date(
      parseInt(parts[0], 10),
      parseInt(parts[1], 10) - 1,
      parseInt(parts[2], 10),
      12,
      0,
      0
    );
    return d.getDay() === 1;
  }

  document.querySelectorAll('[data-wa-link]').forEach(function (el) {
    var preset = el.getAttribute('data-wa-message');
    el.href = waUrl(preset);
    el.setAttribute('target', '_blank');
    el.setAttribute('rel', 'noopener noreferrer');
  });

  var contactEmail = window.RESTAURANT_CONTACT_EMAIL || 'restaurants@nexusfinlabs.com';
  document.querySelectorAll('[data-mailto-link]').forEach(function (el) {
    var card = el.closest('[data-menu-name]');
    var menuName = card ? card.getAttribute('data-menu-name') : '';
    var subject = 'Consulta menú ' + (menuName || 'degustación');
    var body =
      'Hola,\n\n' +
      'Escribo con una pregunta sobre el menú «' +
      (menuName || '—') +
      '».\n\n';
    el.href =
      'mailto:' +
      contactEmail +
      '?subject=' +
      encodeURIComponent(subject) +
      '&body=' +
      encodeURIComponent(body);
    el.setAttribute('target', '_blank');
    el.setAttribute('rel', 'noopener noreferrer');
  });

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
      dotsWrap.querySelectorAll('.menu-carousel__dot').forEach(function (dot, di) {
        dot.setAttribute('aria-current', di === i ? 'true' : 'false');
      });
    }

    dotsWrap.innerHTML = '';
    for (var d = 0; d < n; d++) {
      (function (di) {
        var dot = document.createElement('button');
        dot.type = 'button';
        dot.className = 'menu-carousel__dot';
        dot.setAttribute('aria-label', 'Foto ' + (di + 1));
        dot.addEventListener('click', function () {
          go(di);
        });
        dotsWrap.appendChild(dot);
      })(d);
    }
    go(0);

    if (prev) prev.addEventListener('click', function () { go(i - 1); });
    if (next) next.addEventListener('click', function () { go(i + 1); });
  }

  document.querySelectorAll('[data-carousel]').forEach(initCarousel);

  /* --- Modal reserva --- */
  var modal = document.getElementById('booking-modal');
  if (!modal) return;

  var menuLabel = document.getElementById('booking-modal-menu');
  var dateInput = document.getElementById('booking-date');
  var dateError = document.getElementById('booking-date-error');
  var slotsWrap = document.getElementById('booking-slots');
  var phoneInput = document.getElementById('booking-phone');
  var phoneError = document.getElementById('booking-phone-error');
  var emailInput = document.getElementById('booking-email');
  var emailError = document.getElementById('booking-email-error');
  var summaryEl = document.getElementById('booking-summary');
  var stripeHint = document.getElementById('booking-stripe-hint');
  var copyBtn = document.getElementById('booking-copy-summary');
  var waFallback = document.getElementById('booking-wa-fallback');

  var state = {
    menuName: '',
    date: '',
    slot: null,
    phone: '',
    email: '',
  };

  function showStep(name) {
    modal.querySelectorAll('.booking-step').forEach(function (step) {
      step.hidden = step.getAttribute('data-step') !== name;
    });
  }

  function openModal(card) {
    state.menuName = card.getAttribute('data-menu-name') || 'Menú';
    menuLabel.textContent = state.menuName;
    state.date = '';
    state.slot = null;
    state.phone = '';
    state.email = '';
    dateInput.value = '';
    phoneInput.value = '';
    if (emailInput) emailInput.value = '';
    dateError.hidden = true;
    phoneError.hidden = true;
    if (emailError) emailError.hidden = true;
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
        slotsWrap.querySelectorAll('.slot-btn').forEach(function (b) {
          b.classList.remove('is-selected');
        });
        btn.classList.add('is-selected');
        showStep('phone');
      });
      slotsWrap.appendChild(btn);
    });
  }

  function buildSummary() {
    return (
      'Menú: ' +
      state.menuName +
      '\n' +
      'Fecha: ' +
      state.date +
      '\n' +
      'Turno: ' +
      (state.slot ? state.slot.label : '') +
      '\n' +
      'Teléfono: ' +
      state.phone
    );
  }

  function buildReferenceId() {
    return (
      'NEXUS_LOUNGE|' +
      state.menuName.replace(/\|/g, '') +
      '|' +
      state.date +
      '|' +
      (state.slot ? state.slot.value : '') +
      '|' +
      state.phone.replace(/\s/g, '')
    );
  }

  function stripeUrlWithRef() {
    var base = (window.STRIPE_BOOKING_URL || '').trim();
    if (!base) return '';
    var ref = buildReferenceId();
    var sep = base.indexOf('?') >= 0 ? '&' : '?';
    return base + sep + 'client_reference_id=' + encodeURIComponent(ref);
  }

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
        if (!v) {
          dateError.textContent = 'Selecciona una fecha.';
          dateError.hidden = false;
          return;
        }
        if (isMondayDateString(v)) {
          dateError.textContent = 'Los lunes cerramos. Elige otro día.';
          dateError.hidden = false;
          return;
        }
        dateError.hidden = true;
        state.date = v;
        renderSlots();
        showStep('slot');
        return;
      }
      if (target === 'date') {
        showStep('date');
        return;
      }
      if (target === 'phone') {
        showStep('phone');
      }
      if (target === 'email') {
        showStep('email');
      }
    });
  });

  dateInput.addEventListener('change', function () {
    var v = dateInput.value;
    if (v && isMondayDateString(v)) {
      dateError.textContent = 'Los lunes cerramos. Elige otro día.';
      dateError.hidden = false;
    } else {
      dateError.hidden = true;
    }
  });

  // ── Phone step: just collect phone, go to email step ──────────
  document.getElementById('booking-phone-next').addEventListener('click', function () {
    var raw = (phoneInput.value || '').trim();
    var digits = raw.replace(/\D/g, '');
    if (digits.length < 9) {
      phoneError.textContent = 'Introduce un teléfono válido (mín. 9 dígitos).';
      phoneError.hidden = false;
      return;
    }
    phoneError.hidden = true;
    state.phone = raw;
    showStep('email');
  });

  // ── Email step: validate, call API, show confirmation ──────────
  var emailNextBtn = document.getElementById('booking-email-next');
  if (emailNextBtn) {
    emailNextBtn.addEventListener('click', function () {
      var rawEmail = (emailInput ? emailInput.value : '').trim();
      var emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRe.test(rawEmail)) {
        if (emailError) {
          emailError.textContent = 'Introduce un email válido.';
          emailError.hidden = false;
        }
        return;
      }
      if (emailError) emailError.hidden = true;
      state.email = rawEmail;

      var digits = state.phone.replace(/\D/g, '');
      var startTime = state.slot ? state.slot.value.split('-')[0] : '20:00';

      var apiPayload = {
        name: 'Web-' + digits.slice(-4),
        phone: state.phone,
        email: rawEmail,
        date: state.date,
        time: startTime,
        party_size: 2,
        source: 'web',
        notes: 'Menú: ' + state.menuName + ' | Turno: ' + (state.slot ? state.slot.label : ''),
      };

      // Show loading
      emailNextBtn.textContent = 'Enviando...';
      emailNextBtn.disabled = true;

      fetch('reservations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiPayload),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          state.reservationRef = data.external_ref || '';
          // Clean summary for the modal display
          var displayLines = [
            'Restaurante: Nexus Lounge',
            'Menu: ' + state.menuName,
            'Fecha: ' + state.date + '  ' + (state.slot ? state.slot.label : ''),
            'Personas: ' + guestCount,
            'Tel: ' + state.phone,
            'Email: ' + rawEmail,
            state.reservationRef ? 'Ref: ' + state.reservationRef : '',
          ].filter(Boolean).join('\n');

          if (summaryEl) summaryEl.textContent = displayLines;
          if (stripeHint) stripeHint.textContent = 'Reserva confirmada. Hemos enviado los detalles a ' + rawEmail + '.';

          // WhatsApp message: plain text, no complex multi-byte emojis
          var waMsgLines = [
            'NEXUS LOUNGE - Reserva confirmada',
            '---',
            'Menu: ' + state.menuName,
            'Fecha: ' + state.date,
            'Turno: ' + (state.slot ? state.slot.label : ''),
            'Personas: ' + guestCount,
            'Tel: ' + state.phone,
            'Email: ' + rawEmail,
            state.reservationRef ? 'Ref: ' + state.reservationRef : '',
          ].filter(Boolean).join('%0A');
          waFallback.href = waUrl('NEXUS LOUNGE - Reserva confirmada%0A---%0AMenu: ' + encodeURIComponent(state.menuName) + '%0AFecha: ' + state.date + '%0ATurno: ' + encodeURIComponent(state.slot ? state.slot.label : '') + '%0APersonas: ' + guestCount + '%0ATel: ' + state.phone + '%0AEmail: ' + encodeURIComponent(rawEmail) + (state.reservationRef ? '%0ARef: ' + state.reservationRef : ''));
          showStep('confirm');
        })
        .catch(function () {
          if (summaryEl) summaryEl.textContent = 'Menu: ' + state.menuName + '\nFecha: ' + state.date + '\nTel: ' + state.phone + '\nEmail: ' + rawEmail;
          if (stripeHint) stripeHint.textContent = 'No pudimos registrar la reserva online. Confirma por WhatsApp.';
          waFallback.href = 'https://wa.me/' + (window.RESTAURANT_WHATSAPP || '').replace(/\D/g, '') + '?text=' + encodeURIComponent('NEXUS LOUNGE - Solicitud de reserva\nMenu: ' + state.menuName + '\nFecha: ' + state.date + '\nTel: ' + state.phone);
          showStep('confirm');
        })
        .finally(function () {
          emailNextBtn.textContent = 'Confirmar Reserva';
          emailNextBtn.disabled = false;
        });
    });
  }

  copyBtn.addEventListener('click', function () {
    var text = buildSummary();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        copyBtn.textContent = 'Copiado';
        setTimeout(function () {
          copyBtn.textContent = 'Copiar resumen';
        }, 2000);
      });
    } else {
      window.prompt('Copia el resumen:', text);
    }
  });

  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.nav-main');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('is-open');
    });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        nav.classList.remove('is-open');
      });
    });
  }

  // Go to menu.html on card click
  document.querySelectorAll('.tasting-card').forEach(function(card) {
    card.style.cursor = 'pointer';
    card.addEventListener('click', function(e) {
      if (e.target.closest('.menu-carousel__btn') || 
          e.target.closest('.menu-carousel__dots') || 
          e.target.closest('.btn-wa') || 
          e.target.closest('.btn-book') ||
          e.target.closest('[data-open-booking]')) {
        return;
      }
      var name = card.getAttribute('data-menu-name');
      if (name) {
        window.location.href = 'menu.html?id=' + encodeURIComponent(name);
      }
    });
  });

})();
