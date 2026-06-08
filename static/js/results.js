/*
 * SELF-AUDIT
 * ----------
 * File: results.js
 * Purpose: Results-page interactivity — row expand/collapse detail panels,
 *          score-cell colouring, column sorting, min-score filter, CSV export,
 *          search input, and scroll synchronisation.
 * eval() / exec(): NONE.
 * Frameworks: NONE — vanilla JavaScript only.
 */

/* =====================================================================
 * 1. DOM-READY BOOTSTRAP
 * ===================================================================== */
document.addEventListener('DOMContentLoaded', function () {
  colorScoreCells();
  initRowDetails();
  initColumnSort();
  initScoreFilter();
  initSearchFilter();
  initExportCSV();
  initScrollSync();
});

/* =====================================================================
 * 2. SCORE CELL COLOURING
 * ===================================================================== */

/** Thresholds for score classification — see results_table.css */
var SCORE_HIGH_THRESHOLD   = 0.7;
var SCORE_MEDIUM_THRESHOLD = 0.4;

/**
 * Walk every cell with data-score, parse the float, and apply the
 * appropriate CSS class (.score-high / .score-medium / .score-low).
 */
function colorScoreCells() {
  var cells = document.querySelectorAll('[data-score]');
  cells.forEach(function (cell) {
    var raw = cell.getAttribute('data-score');
    if (raw === '' || raw === 'N/A') return;

    var value = parseFloat(raw);
    if (isNaN(value)) return;

    cell.classList.remove('score-high', 'score-medium', 'score-low');
    if (value >= SCORE_HIGH_THRESHOLD) {
      cell.classList.add('score-high');
    } else if (value >= SCORE_MEDIUM_THRESHOLD) {
      cell.classList.add('score-medium');
    } else {
      cell.classList.add('score-low');
    }
  });
}

/* =====================================================================
 * 3. ROW CLICK → DETAIL PANEL
 * ===================================================================== */

function initRowDetails() {
  var dataRows = document.querySelectorAll('.results-table tbody tr.data-row');

  dataRows.forEach(function (row) {
    row.addEventListener('click', function () {
      var detailId  = row.getAttribute('data-detail');
      var detailRow = document.getElementById(detailId);
      if (!detailRow) return;

      var isVisible = detailRow.classList.contains('visible');

      /* Close all detail rows first (accordion behaviour) */
      document.querySelectorAll('.detail-row.visible').forEach(function (dr) {
        dr.classList.remove('visible');
      });
      document.querySelectorAll('.data-row.row-selected').forEach(function (sr) {
        sr.classList.remove('row-selected');
      });

      /* Toggle the clicked one */
      if (!isVisible) {
        detailRow.classList.add('visible');
        row.classList.add('row-selected');
      }
    });
  });
}

/* =====================================================================
 * 4. COLUMN SORT
 * ===================================================================== */

function initColumnSort() {
  var table = document.querySelector('.results-table');
  if (!table) return;

  var headers = table.querySelectorAll('thead th[data-sort]');

  headers.forEach(function (th, colIndex) {
    th.addEventListener('click', function () {
      var key       = th.getAttribute('data-sort');
      var tbody     = table.querySelector('tbody');
      var rows      = Array.from(tbody.querySelectorAll('tr.data-row'));
      var ascending = !th.classList.contains('sorted-asc');

      /* Clear all sort indicators */
      headers.forEach(function (h) {
        h.classList.remove('sorted-asc', 'sorted-desc');
      });
      th.classList.add(ascending ? 'sorted-asc' : 'sorted-desc');

      rows.sort(function (a, b) {
        var aVal = getCellSortValue(a, key);
        var bVal = getCellSortValue(b, key);

        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return ascending ? aVal - bVal : bVal - aVal;
        }
        var aStr = String(aVal).toLowerCase();
        var bStr = String(bVal).toLowerCase();
        if (aStr < bStr) return ascending ? -1 : 1;
        if (aStr > bStr) return ascending ? 1 : -1;
        return 0;
      });

      /* Reattach sorted rows (each data-row + its detail-row) */
      rows.forEach(function (row) {
        var detailId  = row.getAttribute('data-detail');
        var detailRow = detailId ? document.getElementById(detailId) : null;
        tbody.appendChild(row);
        if (detailRow) tbody.appendChild(detailRow);
      });
    });
  });
}

/**
 * Extract a sortable value from a data-row by column key.
 *
 * @param {HTMLTableRowElement} row
 * @param {string} key
 * @returns {number|string}
 */
function getCellSortValue(row, key) {
  var cell = row.querySelector('[data-col="' + key + '"]');
  if (!cell) return '';

  var score = cell.getAttribute('data-score');
  if (score !== null && score !== '' && score !== 'N/A') {
    var num = parseFloat(score);
    if (!isNaN(num)) return num;
  }

  var raw = cell.getAttribute('data-value');
  if (raw !== null) {
    var num2 = parseFloat(raw);
    return isNaN(num2) ? raw : num2;
  }

  var text = cell.textContent.trim();
  var num3 = parseFloat(text);
  return isNaN(num3) ? text : num3;
}

/* =====================================================================
 * 5. MINIMUM SCORE FILTER
 * ===================================================================== */

function initScoreFilter() {
  var filterInput = document.getElementById('min-score-filter');
  if (!filterInput) return;

  filterInput.addEventListener('input', function () {
    applyFilters();
  });
}

/**
 * Central filter application — combines min-score and search text.
 */
function applyFilters() {
  var filterInput = document.getElementById('min-score-filter');
  var searchInput = document.getElementById('search-filter');
  var minScore    = filterInput ? parseFloat(filterInput.value) : 0;
  var searchText  = searchInput ? searchInput.value.trim().toUpperCase() : '';
  var rows        = document.querySelectorAll('.results-table tbody tr.data-row');
  var visibleCount = 0;

  if (isNaN(minScore)) minScore = 0;

  rows.forEach(function (row) {
    var detailId  = row.getAttribute('data-detail');
    var detailRow = detailId ? document.getElementById(detailId) : null;

    var passScore  = true;
    var passSearch = true;

    /* Score filter: check the "final_score" column */
    var finalCell = row.querySelector('[data-col="final_score"]');
    if (finalCell) {
      var scoreVal = parseFloat(finalCell.getAttribute('data-score'));
      if (!isNaN(scoreVal) && scoreVal < minScore) {
        passScore = false;
      }
    }

    /* Search filter: check spacer sequences */
    if (searchText.length > 0) {
      var spacerA = row.querySelector('[data-col="spacer_a"]');
      var spacerB = row.querySelector('[data-col="spacer_b"]');
      var textA   = spacerA ? spacerA.textContent.toUpperCase() : '';
      var textB   = spacerB ? spacerB.textContent.toUpperCase() : '';
      if (textA.indexOf(searchText) === -1 && textB.indexOf(searchText) === -1) {
        passSearch = false;
      }
    }

    var show = passScore && passSearch;
    row.classList.toggle('hidden', !show);
    if (detailRow) {
      detailRow.classList.toggle('hidden', !show);
      if (!show) detailRow.classList.remove('visible');
    }
    if (show) visibleCount++;
  });

  /* Update the count display */
  var countEl = document.getElementById('results-count');
  if (countEl) {
    countEl.textContent = visibleCount + ' pair' + (visibleCount !== 1 ? 's' : '') + ' shown';
  }
}

/* =====================================================================
 * 6. SEARCH / FILTER INPUT
 * ===================================================================== */

function initSearchFilter() {
  var searchInput = document.getElementById('search-filter');
  if (!searchInput) return;

  searchInput.addEventListener('input', function () {
    applyFilters();
  });
}

/* =====================================================================
 * 7. CSV EXPORT
 * ===================================================================== */

function initExportCSV() {
  var exportBtn = document.getElementById('export-csv-btn');
  if (!exportBtn) return;

  exportBtn.addEventListener('click', function () {
    var table = document.querySelector('.results-table');
    if (!table) return;

    var csvRows = [];

    /* Header */
    var headers = [];
    table.querySelectorAll('thead th[data-sort]').forEach(function (th) {
      headers.push(escapeCSV(th.textContent.trim()));
    });
    csvRows.push(headers.join(','));

    /* Visible data rows */
    table.querySelectorAll('tbody tr.data-row:not(.hidden)').forEach(function (row) {
      var cells = [];
      row.querySelectorAll('td').forEach(function (td) {
        if (td.classList.contains('col-rank')) {
          cells.push(escapeCSV(td.textContent.trim()));
        } else {
          var val = td.getAttribute('data-value') || td.getAttribute('data-score') || td.textContent.trim();
          cells.push(escapeCSV(val));
        }
      });
      csvRows.push(cells.join(','));
    });

    var csvContent = csvRows.join('\n');
    var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    var url  = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'tigr_tas_results.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  });
}

/**
 * Escape a value for safe inclusion in CSV.
 *
 * @param {string} value
 * @returns {string}
 */
function escapeCSV(value) {
  if (value === null || value === undefined) return '';
  var str = String(value);
  if (str.indexOf(',') !== -1 || str.indexOf('"') !== -1 || str.indexOf('\n') !== -1) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

/* =====================================================================
 * 8. SCROLL SYNC — sequence overview ↔ table
 * ===================================================================== */

function initScrollSync() {
  var seqContainer   = document.querySelector('.seq-track-container');
  var tableContainer = document.querySelector('.results-scroll-container');

  if (!seqContainer || !tableContainer) return;

  var syncing = false;

  seqContainer.addEventListener('scroll', function () {
    if (syncing) return;
    syncing = true;
    var ratio = seqContainer.scrollLeft / Math.max(1, seqContainer.scrollWidth - seqContainer.clientWidth);
    tableContainer.scrollLeft = ratio * (tableContainer.scrollWidth - tableContainer.clientWidth);
    requestAnimationFrame(function () { syncing = false; });
  });

  tableContainer.addEventListener('scroll', function () {
    if (syncing) return;
    syncing = true;
    var ratio = tableContainer.scrollLeft / Math.max(1, tableContainer.scrollWidth - tableContainer.clientWidth);
    seqContainer.scrollLeft = ratio * (seqContainer.scrollWidth - seqContainer.clientWidth);
    requestAnimationFrame(function () { syncing = false; });
  });
}
