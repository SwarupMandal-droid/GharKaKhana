/* ── GharKhana — main.js (Production 2026) ──────────────────── */

document.addEventListener('DOMContentLoaded', function () {

  /* ── 1. Auto-dismiss messages after 5 seconds ───────────────── */
  document.querySelectorAll('.message').forEach(function (msg) {
    setTimeout(function () {
      msg.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(20px)';
      setTimeout(function () { msg.remove(); }, 420);
    }, 5000);
  });

  /* ── 2. Confirm before destructive actions ───────────────────── */
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  /* ── 3. Capacity bar — auto colour ──────────────────────────── */
  document.querySelectorAll('.capacity-bar-fill').forEach(function (bar) {
    var pct = parseFloat(bar.style.width);
    if (pct >= 100) bar.classList.add('full');
    else if (pct >= 75) bar.classList.add('warn');
  });

  /* ── 4. Quantity controls on cart / menu pages ───────────────── */
  document.querySelectorAll('.qty-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = document.querySelector(btn.dataset.target);
      if (!input) return;
      var val = parseInt(input.value) || 0;
      var min = parseInt(input.min) || 0;
      var max = parseInt(input.max) || 99;
      if (btn.dataset.action === 'inc') input.value = Math.min(val + 1, max);
      if (btn.dataset.action === 'dec') input.value = Math.max(val - 1, min);
      input.dispatchEvent(new Event('change'));
    });
  });

  /* ── 5. Live cart total update ───────────────────────────────── */
  function updateCartTotal() {
    var total = 0;
    document.querySelectorAll('.cart-item-row').forEach(function (row) {
      var qty   = parseInt(row.querySelector('.item-qty')?.value) || 0;
      var price = parseFloat(row.dataset.price) || 0;
      var lineEl = row.querySelector('.item-line-total');
      if (lineEl) lineEl.textContent = '₹' + (qty * price).toFixed(0);
      total += qty * price;
    });
    var subtotalEl = document.getElementById('cart-subtotal');
    if (subtotalEl) subtotalEl.textContent = '₹' + total.toFixed(0);
    var feeEl = document.getElementById('cart-fee');
    if (feeEl) feeEl.textContent = '₹' + (total * 0.002).toFixed(2);
    var totalEl = document.getElementById('cart-total');
    var deliveryCharge = parseFloat(document.getElementById('delivery-charge')?.dataset.charge) || 0;
    if (totalEl) totalEl.textContent = '₹' + (total + total * 0.002 + deliveryCharge).toFixed(0);
  }
  document.querySelectorAll('.item-qty').forEach(function (input) {
    input.addEventListener('change', updateCartTotal);
  });

  /* ── 6. Toggle same-day settings visibility ──────────────────── */
  var sameDayToggle   = document.getElementById('id_same_day_enabled');
  var sameDaySettings = document.getElementById('same-day-settings');
  if (sameDayToggle && sameDaySettings) {
    function toggleSameDay() {
      sameDaySettings.style.display = sameDayToggle.checked ? 'block' : 'none';
    }
    toggleSameDay();
    sameDayToggle.addEventListener('change', toggleSameDay);
  }

  /* ── 7. PIN input — auto format (single field) ───────────────── */
  var pinInput = document.getElementById('pin-input');
  if (pinInput) {
    pinInput.setAttribute('inputmode', 'numeric');
    pinInput.addEventListener('input', function () {
      this.value = this.value.replace(/\D/g, '').slice(0, 4);
    });
  }

  /* ── 8. PIN auto-advance for multi-box inputs (p1–p4) ────────── */
  var pinBoxes = document.querySelectorAll('.pin-box, .pin-digit');
  if (pinBoxes.length > 0) {
    pinBoxes.forEach(function (box, idx) {
      box.setAttribute('inputmode', 'numeric');
      box.addEventListener('input', function (e) {
        this.value = this.value.replace(/\D/g, '').slice(0, 1);
        if (this.value && idx < pinBoxes.length - 1) {
          pinBoxes[idx + 1].focus();
        }
      });
      box.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace' && !this.value && idx > 0) {
          pinBoxes[idx - 1].focus();
        }
      });
    });
  }

  /* ── 9. Booking animation — show on order confirm page ─────────── */
  var bookingAnim = document.getElementById('booking-animation');
  if (bookingAnim) bookingAnim.classList.add('animate-in');

  /* ── 10. Photo upload — food-tech hero style ─────────────────── */
  document.querySelectorAll('.photo-upload-input').forEach(function (input) {
    input.addEventListener('change', function () {
      if (this.files && this.files[0]) {
        var file = this.files[0];
        var clearInput  = document.getElementById('clear-photo-input');
        if (clearInput) clearInput.value = 'false';

        var previewId   = this.dataset.preview || 'preview-img';
        var labelId     = this.dataset.label   || 'photo-filename-label';

        var reader = new FileReader();
        reader.onload = function (e) {
          var previewImg    = document.getElementById(previewId);
          var placeholder   = document.getElementById('preview-placeholder');
          var successBadge  = document.getElementById('upload-success-badge');
          var label         = document.getElementById(labelId);

          if (previewImg) {
            if (previewImg.tagName.toLowerCase() === 'img') {
              previewImg.src = e.target.result;
              previewImg.style.display = 'block';
              previewImg.style.opacity = '0';
              previewImg.style.transform = 'scale(1.05)';
            } else {
              previewImg.style.backgroundImage = 'url(' + e.target.result + ')';
              previewImg.style.backgroundSize  = 'cover';
              previewImg.style.backgroundPosition = 'center';
              previewImg.innerHTML = '';
            }

            if (placeholder) placeholder.style.display = 'none';

            setTimeout(function () {
              previewImg.style.transition = 'all 0.6s cubic-bezier(0.2, 0, 0, 1)';
              previewImg.style.opacity    = '1';
              previewImg.style.transform  = 'scale(1)';

              if (successBadge) {
                successBadge.classList.add('show');
                setTimeout(function () { successBadge.classList.remove('show'); }, 3000);
              }
            }, 50);
          }

          if (label) {
            var name = file.name.length > 22 ? file.name.substring(0, 20) + '…' : file.name;
            label.textContent = 'READY: ' + name;
            label.style.color = '#FF6B00';
          }
        };
        reader.readAsDataURL(file);
      }
    });
  });

  /* ── 11. Remove Photo ─────────────────────────────────────────── */
  var removeBtn = document.getElementById('remove-photo-btn');
  if (removeBtn) {
    removeBtn.addEventListener('click', function () {
      var input       = document.getElementById('photo-input');
      var previewImg  = document.getElementById('preview-img');
      var placeholder = document.getElementById('preview-placeholder');
      var label       = document.getElementById('photo-filename-label');
      var clearInput  = document.getElementById('clear-photo-input');

      if (input)      input.value   = '';
      if (clearInput) clearInput.value = 'true';

      if (previewImg) {
        previewImg.style.transition = 'all 0.4s ease';
        previewImg.style.opacity   = '0';
        previewImg.style.transform = 'scale(0.95)';
        setTimeout(function () {
          previewImg.src          = '';
          previewImg.style.display = 'none';
          if (placeholder) placeholder.style.display = 'flex';
        }, 420);
      }

      if (label) {
        label.textContent = 'PHOTO REMOVED';
        label.style.color = '#64748b';
      }
    });
  }

  /* ── 12. Global photo upload trigger ─────────────────────────── */
  document.querySelectorAll('.photo-upload-trigger').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = document.getElementById(btn.dataset.target || 'photo-input');
      if (target) target.click();
    });
  });

  /* ── 13. Update nav cart count from localStorage ─────────────── */
  updateNavCartCount();

  /* ── 14. Mobile Navigation Drawer ────────────────────────────── */
  initMobileNav();

  /* ── 15. Cook List — define missing search helpers ────────────── */
  window.clearSearch = function () {
    var input = document.getElementById('search-input');
    if (input) {
      input.value = '';
      input.form.submit();
    }
  };

  window.clearAllFilters = function () {
    var url = window.location.pathname;
    window.location.href = url;
  };

  /* ── 16. Double-submit guard on all forms ─────────────────────── */
  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function () {
      var submitBtn = form.querySelector('[type="submit"]');
      if (submitBtn && !submitBtn.dataset.allowMultiple) {
        setTimeout(function () {
          submitBtn.disabled = true;
          submitBtn.classList.add('btn-loading');
          var originalText = submitBtn.textContent;
          submitBtn.dataset.originalText = originalText;
          submitBtn.innerHTML =
            '<svg class="animate-spin" style="width:18px;height:18px;margin-right:8px;flex-shrink:0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>'
            + 'Processing...';
        }, 0);
      }
    });
  });

}); /* end DOMContentLoaded */

/* ── Map pin preview — update lat/lng fields from Leaflet ─────── */
window.setMapCoords = function (lat, lng, address) {
  var latField  = document.getElementById('id_latitude');
  var lngField  = document.getElementById('id_longitude');
  var addrField = document.getElementById('id_address');
  if (latField)  latField.value  = lat;
  if (lngField)  lngField.value  = lng;
  if (addrField && address) addrField.value = address;
};

/* ── Mobile Nav Initialization ─────────────────────────────────── */
function initMobileNav() {
  var hamburger   = document.getElementById('hamburger-btn');
  var overlay     = document.getElementById('mobile-nav-overlay');
  var drawer      = document.getElementById('mobile-nav-drawer');
  var closeBtn    = document.getElementById('mobile-nav-close');

  if (!hamburger || !drawer) return;

  function openNav() {
    hamburger.classList.add('open');
    hamburger.setAttribute('aria-expanded', 'true');
    overlay.classList.add('open');
    overlay.setAttribute('aria-hidden', 'false');
    drawer.classList.add('open');
    document.body.style.overflow = 'hidden';

    // Focus first link in drawer
    var firstLink = drawer.querySelector('a, button');
    if (firstLink) setTimeout(function () { firstLink.focus(); }, 50);
  }

  function closeNav() {
    hamburger.classList.remove('open');
    hamburger.setAttribute('aria-expanded', 'false');
    overlay.classList.remove('open');
    overlay.setAttribute('aria-hidden', 'true');
    drawer.classList.remove('open');
    document.body.style.overflow = '';
    hamburger.focus();
  }

  hamburger.addEventListener('click', function () {
    if (drawer.classList.contains('open')) closeNav();
    else openNav();
  });

  if (closeBtn) closeBtn.addEventListener('click', closeNav);
  overlay.addEventListener('click', closeNav);

  // Close on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer.classList.contains('open')) closeNav();
  });

  // Trap focus inside drawer when open
  drawer.addEventListener('keydown', function (e) {
    if (!drawer.classList.contains('open') || e.key !== 'Tab') return;
    var focusable = drawer.querySelectorAll('a[href], button:not([disabled])');
    var first = focusable[0];
    var last  = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });
}

/* ── Update nav cart count badge ──────────────────────────────── */
function updateNavCartCount() {
  var countEl = document.getElementById('nav-cart-count');
  if (!countEl) return;
  try {
    var cart  = JSON.parse(localStorage.getItem('gk_cart') || 'null');
    if (!cart || !cart.items) { countEl.style.display = 'none'; return; }
    var count = Object.values(cart.items).reduce(function (s, it) {
      return s + (parseInt(it.qty) || 0);
    }, 0);
    if (count > 0) {
      countEl.textContent = count > 99 ? '99+' : count;
      countEl.style.display = 'flex';
      countEl.setAttribute('aria-label', count + ' items in cart');
    } else {
      countEl.style.display = 'none';
    }
  } catch (e) {
    countEl.style.display = 'none';
  }
}

/* ── Button loading helpers (used by checkout pages) ──────────── */
window.setButtonLoading = function (btnId, loadingText) {
  var btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = true;
  btn.classList.add('btn-loading');
  btn.dataset.originalText = btn.innerHTML;
  btn.innerHTML = '<svg class="animate-spin" style="width:18px;height:18px;margin-right:8px" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>'
    + (loadingText || 'Processing...');
};

window.clearButtonLoading = function (btnId) {
  var btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = false;
  btn.classList.remove('btn-loading');
  if (btn.dataset.originalText) btn.innerHTML = btn.dataset.originalText;
};

/* ── Inline toast helper (replaces alert() calls) ──────────────── */
window.showToast = function (message, type) {
  type = type || 'info';
  var wrap = document.querySelector('.messages-wrap');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.className = 'messages-wrap';
    wrap.setAttribute('role', 'alert');
    wrap.setAttribute('aria-live', 'polite');
    document.body.appendChild(wrap);
  }
  var el = document.createElement('div');
  el.className = 'message message-' + type;
  el.setAttribute('role', 'status');
  el.innerHTML = '<span>' + message + '</span>'
    + '<button class="message-close" onclick="this.parentElement.remove()" aria-label="Dismiss">×</button>';
  wrap.appendChild(el);
  setTimeout(function () {
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    el.style.opacity = '0';
    el.style.transform = 'translateX(20px)';
    setTimeout(function () { el.remove(); }, 420);
  }, 4000);
};
