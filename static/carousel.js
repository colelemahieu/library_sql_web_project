function scrollCarousel(direction) {
    const container = document.getElementById('carousel');
    const card = container.querySelector('.card');
    if (!card) return;

    const cardWidth = card.offsetWidth + 20; 
    container.scrollBy({ left: direction * cardWidth * 5, behavior: 'smooth' });
}

function updateArrows() {
    const container = document.getElementById('carousel');
    const leftArrow = document.getElementById('arrow-left');
    const rightArrow = document.getElementById('arrow-right');

    const maxScroll = container.scrollWidth - container.clientWidth;

    leftArrow.style.display = container.scrollLeft <= 0 ? 'none' : 'flex';
    rightArrow.style.display = container.scrollLeft >= maxScroll ? 'none' : 'flex';
}


window.addEventListener('load', () => {
    const container = document.getElementById('carousel');
    
    updateArrows();

    container.addEventListener('scroll', updateArrows);
});

