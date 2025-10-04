document.addEventListener("DOMContentLoaded", function () {
  
  const genreColorMap = {
    'Science Fiction': '#0077b6',
    'Fantasy': '#2b9348',
    'Classic': '#a11d33',
    'Fiction': '#8e9aaf',
    'Mystery': '#9d4edd',
    'Historical': '#7f4f24'
  };

  const genreLegend = document.querySelector('.genre-legend');
  const genreSegments = document.querySelectorAll('.genre-segment');
  const booksTable = document.querySelector('#search-table'); 

  if (!booksTable || (!genreLegend && !genreSegments.length)) return;

  let activeGenre = null;

  // Click functionality for bar segments and legend
  function setupClickHandlers(selector) {
    document.querySelectorAll(selector).forEach(el => {
      el.addEventListener('click', () => {
        const genre = el.getAttribute('data-genre');
        toggleGenreFilter(genre, el);
      });
    });
  }

  setupClickHandlers('.genre-segment');
  setupClickHandlers('.genre-legend-item');

  function toggleGenreFilter(genre, clickedEl) {
    // reset after 2nd click
    if (activeGenre === genre) {
      activeGenre = null;
      filterTable(null);
      document.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
      return;
    }

    activeGenre = genre;
    filterTable(genre);

    // Visual highlight for active 
    document.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
    document.querySelectorAll(`[data-genre="${genre}"]`).forEach(el => el.classList.add('active'));
  }

  function filterTable(genre) {
    const rows = booksTable.querySelectorAll('tbody tr');
    rows.forEach(row => {
      const genreCell = row.cells[3]; 
      if (!genreCell) return;

      const rowGenre = genreCell.textContent.trim();
      if (!genre || rowGenre === genre) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  }
});

