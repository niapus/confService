function getCsrfToken() {
   return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

function updateStatus(status, id) {
   if (confirm(`Вы уверены, что хотите ${status === 'accepted' ? 'принять' : 'отклонить'} этот тезис?`)) {
      const formData = new FormData();
      formData.append('status', status);
      formData.append('csrf_token', getCsrfToken());

      fetch(`/admin/theses/${id}/status`, {
         method: 'POST',
         body: formData
      })
      .then(response => {
         if (response.ok) {
            window.location.reload();
         } else {
            alert('Произошла ошибка при обновлении статуса');
         }
      })
      .catch(error => {
         console.error('Error:', error);
         alert('Произошла ошибка при обновлении статуса');
      });
   }
}