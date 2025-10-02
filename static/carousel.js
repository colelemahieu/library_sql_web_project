function scrollCarousel(direction) {
    const container = document.getElementById('carousel');
    const card = container.querySelector('.card');
    if (!card) return;

    const cardWidth = card.offsetWidth + 20; 
    container.scrollBy({ left: direction * cardWidth * 4, behavior: 'smooth' });

    setTimeout(updateArrows, 400);
}

function updateArrows() {
    const container = document.getElementById('carousel');
    const leftArrow = document.getElementById('arrow-left');
    const rightArrow = document.getElementById('arrow-right');

    // Can scroll left?
    leftArrow.disabled = container.scrollLeft <= 0;

    // Can scroll right?
    const maxScroll = container.scrollWidth - container.clientWidth;
    rightArrow.disabled = container.scrollLeft >= maxScroll - 5; // small buffer
}

// Run once on page load
window.addEventListener('load', updateArrows);

