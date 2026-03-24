document.addEventListener('DOMContentLoaded', function() {
   document.querySelectorAll('.timeline-item').forEach((item, index) => {
      item.style.animationDelay = `${index * 0.05}s`;
   });

   document.querySelectorAll('.timeline-date').forEach(date => {
      const eventCount = date.querySelector('.event-count');
      if (eventCount) {
         date.setAttribute('title', `В этот день проводится ${eventCount.textContent}`);
      }
   });
});