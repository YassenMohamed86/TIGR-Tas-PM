/*
 * SELF-AUDIT
 * ----------
 * File: main.js
 * Purpose: Input-page interactivity — tab switching, form validation,
 *          file-upload UX, collapsible advanced options, loading overlay.
 * eval() / exec(): NONE.
 * Frameworks: NONE — vanilla JavaScript only.
 */

/* =====================================================================
 * 1. DOM-READY BOOTSTRAP
 * ===================================================================== */
document.addEventListener('DOMContentLoaded', function () {
  initTabs();
  initFileUpload();
  initAdvancedToggle();
  initFormValidation();
});

/* =====================================================================
 * 2. TAB TOGGLE
 * ===================================================================== */

/**
 * Initialise tab switching between input modes:
 *   raw_sequence | fasta_upload | ncbi_fetch | ensembl_fetch
 *
 * Clicking a tab:
 *   - marks it .active, removes .active from siblings
 *   - shows corresponding .tab-panel, hides others
 *   - writes the input_type value into the hidden field
 */
function initTabs() {
  var tabButtons = document.querySelectorAll('.tab-btn[data-tab]');
  var tabPanels  = document.querySelectorAll('.tab-panel');
  var hiddenType = document.getElementById('input_type');

  if (!tabButtons.length) return;

  tabButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = btn.getAttribute('data-tab');

      /* Toggle active button */
      tabButtons.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');

      /* Toggle visible panel */
      tabPanels.forEach(function (panel) {
        if (panel.getAttribute('data-panel') === target) {
          panel.classList.remove('hidden');
        } else {
          panel.classList.add('hidden');
        }
      });

      /* Sync hidden field */
      if (hiddenType) {
        hiddenType.value = target;
      }
    });
  });
}

/* =====================================================================
 * 3. FILE UPLOAD — display selected filename
 * ===================================================================== */

function initFileUpload() {
  var fileInput = document.getElementById('fasta_file');
  var fileLabel = document.getElementById('file-label');

  if (!fileInput || !fileLabel) return;

  fileInput.addEventListener('change', function () {
    if (fileInput.files.length > 0) {
      fileLabel.textContent = fileInput.files[0].name;
      fileLabel.classList.add('file-selected');
    } else {
      fileLabel.textContent = 'No file chosen';
      fileLabel.classList.remove('file-selected');
    }
  });
}

/* =====================================================================
 * 4. ADVANCED OPTIONS COLLAPSE
 * ===================================================================== */

function initAdvancedToggle() {
  var toggle  = document.getElementById('advanced-toggle');
  var content = document.getElementById('advanced-content');

  if (!toggle || !content) return;

  toggle.addEventListener('click', function () {
    var isExpanded = toggle.classList.toggle('expanded');
    content.classList.toggle('hidden', !isExpanded);
    toggle.setAttribute('aria-expanded', String(isExpanded));
  });
}

/* =====================================================================
 * 5. FORM VALIDATION
 * ===================================================================== */

function initFormValidation() {
  var form = document.getElementById('analysis-form');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    var inputType = document.getElementById('input_type').value;
    var errorMsg  = validateByType(inputType);

    if (errorMsg) {
      e.preventDefault();
      showValidationError(errorMsg);
      return;
    }

    /* Validation passed — show loading spinner */
    showLoadingOverlay();
  });
}

/**
 * Return an error string if validation fails, or null if valid.
 *
 * @param {string} inputType - One of raw_sequence, fasta_upload, ncbi_fetch, ensembl_fetch
 * @returns {string|null}
 */
function validateByType(inputType) {
  switch (inputType) {
    case 'raw_sequence': {
      var seq = document.getElementById('raw_sequence');
      if (!seq || seq.value.trim().length === 0) {
        return 'Please enter a DNA sequence.';
      }
      /* Basic character check — allow ACGTURYSWKMBDHVN and whitespace */
      var cleaned = seq.value.replace(/\s+/g, '').toUpperCase();
      if (!/^[ACGTURYSWKMBDHVN]+$/.test(cleaned)) {
        return 'Sequence contains invalid characters. Only IUPAC nucleotide codes (A, C, G, T, U, …) are allowed.';
      }
      return null;
    }

    case 'fasta_upload': {
      var file = document.getElementById('fasta_file');
      if (!file || file.files.length === 0) {
        return 'Please select a FASTA file to upload.';
      }
      return null;
    }

    case 'ncbi_fetch': {
      var gene     = document.getElementById('ncbi_gene');
      var organism = document.getElementById('ncbi_organism');
      if (!gene || gene.value.trim().length === 0) {
        return 'Please enter a gene name for NCBI lookup.';
      }
      if (!organism || organism.value.trim().length === 0) {
        return 'Please enter an organism name for NCBI lookup.';
      }
      return null;
    }

    case 'ensembl_fetch': {
      var geneId = document.getElementById('ensembl_gene_id');
      if (!geneId || geneId.value.trim().length === 0) {
        return 'Please enter an Ensembl Gene ID (e.g. ENSG00000141510).';
      }
      return null;
    }

    default:
      return 'Unknown input type. Please select a valid input tab.';
  }
}

/**
 * Show an inline validation error above the form submit button.
 *
 * @param {string} message
 */
function showValidationError(message) {
  /* Remove any previous validation error */
  var existing = document.getElementById('validation-error');
  if (existing) existing.remove();

  var errorDiv = document.createElement('div');
  errorDiv.id = 'validation-error';
  errorDiv.className = 'error-message';
  errorDiv.setAttribute('role', 'alert');
  errorDiv.textContent = message;

  var submitArea = document.getElementById('submit-area');
  if (submitArea) {
    submitArea.parentNode.insertBefore(errorDiv, submitArea);
  }

  /* Auto-dismiss after 6 seconds */
  setTimeout(function () {
    if (errorDiv.parentNode) {
      errorDiv.remove();
    }
  }, 6000);
}

/* =====================================================================
 * 6. LOADING OVERLAY
 * ===================================================================== */

function showLoadingOverlay() {
  var overlay = document.createElement('div');
  overlay.className = 'spinner-overlay';
  overlay.id = 'loading-overlay';

  var wrapper = document.createElement('div');
  wrapper.setAttribute('role', 'status');

  var spinner = document.createElement('div');
  spinner.className = 'spinner';

  var text = document.createElement('div');
  text.className = 'spinner-text';
  text.textContent = 'Analyzing sequence\u2026';

  wrapper.appendChild(spinner);
  wrapper.appendChild(text);
  overlay.appendChild(wrapper);
  document.body.appendChild(overlay);
}
