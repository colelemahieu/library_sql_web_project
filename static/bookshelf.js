function renderShelf(percentageRead) {
  const shelf = document.getElementById("shelf");
  const booksContainer = document.getElementById("books");

  // Clear old book
  booksContainer.innerHTML = "";

  const shelfWidth = shelf.offsetWidth - 20; // account for padding
  const baseBookWidth = 22; // width + margin
  const fillWidth = shelfWidth * (percentageRead / 100);

  let booksToShow = Math.floor(fillWidth / baseBookWidth);
  if (booksToShow < 1 && percentageRead > 0) booksToShow = 1;

  for (let i = 0; i < booksToShow; i++) {
    const book = document.createElement("div");
    book.classList.add("book");

    // Random height between 75–90% of shelf height
    const heightPercent = Math.floor(Math.random() * 15) + 75;
    book.style.height = heightPercent + "%";

    book.style.backgroundColor = "#33468a";

    // 2 ridges, evenly spaced in top 10–25%
    const ridgeMin = 10; // top 10%
    const ridgeMax = 25; // bottom 25%
    const lineCount = 2;

    for (let j = 0; j < lineCount; j++) {
      const line = document.createElement("div");
      line.classList.add("book-line");

      // Evenly spaced in ridgeMin → ridgeMax
      const topPercent = ridgeMin + ((ridgeMax - ridgeMin) / (lineCount + 1)) * (j + 1);
      line.style.top = topPercent + "%";

      book.appendChild(line);
    }

    // Append book to container
    booksContainer.appendChild(book);
  }
}

// Run on load
document.addEventListener("DOMContentLoaded", () => {
  const shelfElement = document.getElementById("shelf");
  const percentage = parseInt(shelfElement.dataset.percentage);
  renderShelf(percentage);
});

