function scrollCarousel(direction) {
    const container = document.getElementById('carousel');
    const card = container.querySelector('.card');
    if (!card) return;

    const cardWidth = card.offsetWidth + 20; 
    container.scrollBy({ left: direction * cardWidth * 4, behavior: 'smooth' });
}

// Update the arrow buttons
function updateArrows() {
    const container = document.getElementById('carousel');
    const leftArrow = document.getElementById('arrow-left');
    const rightArrow = document.getElementById('arrow-right');

    const maxScroll = container.scrollWidth - container.clientWidth;

    // Hide arrows when you can't scroll
    leftArrow.style.display = container.scrollLeft <= 0 ? 'none' : 'flex';
    rightArrow.style.display = container.scrollLeft >= maxScroll ? 'none' : 'flex';
}

// Run once on page load
window.addEventListener('load', () => {
    const container = document.getElementById('carousel');
    
    // Update arrows on page load
    updateArrows();

    // Update arrows on scroll instantly
    container.addEventListener('scroll', updateArrows);
});

