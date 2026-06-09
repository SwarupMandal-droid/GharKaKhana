/* GharKhana — main.js */

/* Auto-dismiss messages after 4 seconds */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.message').forEach(function (msg) {
    setTimeout(function () {
      msg.style.opacity = '0';
      msg.style.transition = 'opacity .4s';
      setTimeout(function () { msg.remove(); }, 400);
    }, 4000);
  });
});

/* Confirm before destructive actions */
document.querySelectorAll('[data-confirm]').forEach(function (el) {
  el.addEventListener('click', function (e) {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

/* Capacity bar — auto colour */
document.querySelectorAll('.capacity-bar-fill').forEach(function (bar) {
  var pct = parseFloat(bar.style.width);
  if (pct >= 100) bar.classList.add('full');
  else if (pct >= 75) bar.classList.add('warn');
});

/* Quantity controls on cart / menu pages */
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

/* Live cart total update */
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

/* Toggle same-day settings visibility */
var sameDayToggle = document.getElementById('id_same_day_enabled');
var sameDaySettings = document.getElementById('same-day-settings');
if (sameDayToggle && sameDaySettings) {
  function toggleSameDay() {
    sameDaySettings.style.display = sameDayToggle.checked ? 'block' : 'none';
  }
  toggleSameDay();
  sameDayToggle.addEventListener('change', toggleSameDay);
}

/* PIN input — auto format with spacing */
var pinInput = document.getElementById('pin-input');
if (pinInput) {
  pinInput.addEventListener('input', function () {
    this.value = this.value.replace(/\D/g, '').slice(0, 4);
  });
}

/* NEW: PIN auto-advance for multi-box inputs (p1-p4) */
var pinBoxes = document.querySelectorAll('.pin-box');
if (pinBoxes.length > 0) {
  pinBoxes.forEach(function (box, idx) {
    box.addEventListener('input', function (e) {
      if (box.value.length === 1 && idx < pinBoxes.length - 1) {
        pinBoxes[idx + 1].focus();
      }
    });
    box.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace' && !box.value && idx > 0) {
        pinBoxes[idx - 1].focus();
      }
    });
  });
}

/* Booking animation — show on order confirm page */
var bookingAnim = document.getElementById('booking-animation');
if (bookingAnim) {
  bookingAnim.classList.add('animate-in');
}

/* Map pin preview — update lat/lng fields from Leaflet */
window.setMapCoords = function (lat, lng, address) {
  var latField  = document.getElementById('id_latitude');
  var lngField  = document.getElementById('id_longitude');
  var addrField = document.getElementById('id_address');
  if (latField)  latField.value  = lat;
  if (lngField)  lngField.value  = lng;
  if (addrField && address) addrField.value = address;
};

// Food-Tech Hero Photo Upload Logic
document.querySelectorAll('.photo-upload-input').forEach(function(input) {
  input.addEventListener('change', function() {
    if (this.files && this.files[0]) {
      const file = this.files[0];
      const clearInput = document.getElementById('clear-photo-input');
      if (clearInput) clearInput.value = 'false';

      // Read target IDs from dataset or use defaults for settings.html
      const previewId = this.dataset.preview || 'preview-img';
      const labelId = this.dataset.label || 'photo-filename-label';

      // Simulate upload and show preview
      const reader = new FileReader();
      reader.onload = function(e) {
        const previewImg = document.getElementById(previewId);
        const placeholder = document.getElementById('preview-placeholder');
        const successBadge = document.getElementById('upload-success-badge');
        const label = document.getElementById(labelId);
        
        if (previewImg) {
          if (previewImg.tagName.toLowerCase() === 'img') {
            previewImg.src = e.target.result;
            previewImg.style.display = 'block';
            previewImg.style.opacity = '0';
            previewImg.style.transform = 'scale(1.1)';
          } else {
            previewImg.style.backgroundImage = 'url(' + e.target.result + ')';
            previewImg.style.backgroundSize = 'cover';
            previewImg.style.backgroundPosition = 'center';
            previewImg.innerHTML = '';
          }
          
          if (placeholder) placeholder.style.display = 'none';

          // Animate in
          setTimeout(() => {
            previewImg.style.transition = 'all 0.8s cubic-bezier(0.2, 0, 0, 1)';
            previewImg.style.opacity = '1';
            previewImg.style.transform = 'scale(1)';
            
            // Show success badge
            if (successBadge) {
              successBadge.classList.add('show');
              setTimeout(() => successBadge.classList.remove('show'), 3000);
            }
          }, 50);
        }
        
        if (label) {
          label.textContent = 'READY: ' + file.name.substring(0, 20) + '...';
          label.style.color = '#FF6B00';
        }
      };
      reader.readAsDataURL(file);
    }
  });
});

// Remove Photo Functionality (Hero Style)
const removeBtn = document.getElementById('remove-photo-btn');
if (removeBtn) {
  removeBtn.addEventListener('click', function() {
    const input = document.getElementById('photo-input');
    const previewImg = document.getElementById('preview-img');
    const placeholder = document.getElementById('preview-placeholder');
    const label = document.getElementById('photo-filename-label');
    const clearInput = document.getElementById('clear-photo-input');

    if (input) input.value = '';
    if (clearInput) clearInput.value = 'true';
    
    if (previewImg) {
      previewImg.style.opacity = '0';
      previewImg.style.transform = 'scale(0.95)';
      setTimeout(() => {
        previewImg.src = '';
        previewImg.style.display = 'none';
        if (placeholder) placeholder.style.display = 'flex';
      }, 400);
    }
    
    if (label) {
      label.textContent = 'PHOTO REMOVED';
      label.style.color = '#64748b';
    }
  });
}

// Global upload trigger
document.querySelectorAll('.photo-upload-trigger').forEach(function(btn) {
  btn.addEventListener('click', function() {
    const target = document.getElementById(btn.dataset.target);
    if (target) target.click();
  });
});
