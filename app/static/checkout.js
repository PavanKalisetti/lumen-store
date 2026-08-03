function lineTotals() {
  var nodes = document.querySelectorAll('[data-line]');
  var rows = [];
  for (var i = 0; i < nodes.length; i += 1) {
    rows.push({
      quantity: parseInt(nodes[i].getAttribute('data-quantity'), 10) || 0,
      unit: parseInt(nodes[i].getAttribute('data-unit'), 10) || 0
    });
  }
  return rows;
}

function computeTotal(rows) {
  var total = 0;
  for (var i = 0; i < rows.length; i += 1) {
    total += rows[i].quantity * rows[i].unit;
  }
  return total;
}

function deriveNonce(salt, total) {
  var digits = String(total);
  var span = Math.max(salt.length, digits.length);
  var merged = '';
  for (var i = 0; i < span; i += 1) {
    if (i < salt.length) {
      merged += salt.charAt(i);
    }
    if (i < digits.length) {
      merged += digits.charAt(i);
    }
  }
  var out = '';
  for (var j = 0; j < merged.length; j += 1) {
    var hex = merged.charCodeAt(j).toString(16);
    out += hex.length < 2 ? '0' + hex : hex;
  }
  return out;
}

function attach() {
  var panel = document.querySelector('[data-salt]');
  if (!panel) {
    return;
  }
  var totalField = panel.querySelector('input[name="total_cents"]');
  var nonceField = panel.querySelector('input[name="nonce"]');
  if (!totalField || !nonceField) {
    return;
  }
  var salt = panel.getAttribute('data-salt');
  var total = computeTotal(lineTotals());
  totalField.value = String(total);
  nonceField.value = deriveNonce(salt, total);
  var readout = panel.querySelector('[data-grand]');
  if (readout) {
    readout.textContent = '$' + (total / 100).toFixed(2);
  }
}

document.addEventListener('DOMContentLoaded', attach);
