function togglePopup() {
    const popup = document.getElementById('popup-1');
    popup.classList.toggle('active'); // Toggle the active class on the popup

    const overlay = document.querySelector('.overlay');
    overlay.classList.toggle('active'); // Toggle the active class on the overlay
}
