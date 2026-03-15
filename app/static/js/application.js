document.addEventListener('DOMContentLoaded', function() {
   const workerCheckbox = document.getElementById('status-worker');
   const studentCheckbox = document.getElementById('status-student');
   
   if (workerCheckbox && studentCheckbox) {
      const workGroup = document.getElementById('work-place-group');
      const studyGroup = document.getElementById('study-place-group');
      
      const workInputs = workGroup.querySelectorAll('input');
      const studyInputs = studyGroup.querySelectorAll('input');

      function updateFields() {
         if (workerCheckbox.checked) {
            workGroup.style.display = 'block';
            workInputs.forEach(input => input.required = true);
         } else {
            workGroup.style.display = 'none';
            workInputs.forEach(input => {
               input.required = false;
               input.value = '';
            });
         }

         if (studentCheckbox.checked) {
            studyGroup.style.display = 'block';
            studyInputs.forEach(input => input.required = true);
         } else {
            studyGroup.style.display = 'none';
            studyInputs.forEach(input => {
               input.required = false;
               input.value = '';
            });
         }
      }

      workerCheckbox.addEventListener('change', updateFields);
      studentCheckbox.addEventListener('change', updateFields);
      
      updateFields();
   }

   const thesisForm = document.getElementById('thesis-form');
   
   if (thesisForm) {
      const fileInput = thesisForm.querySelector('input[type="file"]');
      const submitBtn = thesisForm.querySelector('button[type="submit"]');

      if (fileInput) {
         fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;
            
            const fileName = file.name.toLowerCase();
            const allowedExtensions = ['.pdf', '.doc', '.docx'];
            const isValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
            
            if (!isValidExtension) {
               alert('Разрешены только файлы PDF, DOC или DOCX');
               this.value = '';
               return;
            }
            
            if (file.size > 10 * 1024 * 1024) {
               alert('Максимальный размер файла 10 МБ');
               this.value = '';
            }
         });
      }

      if (submitBtn) {
         thesisForm.addEventListener('submit', function() {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
         });
      }
   }
});