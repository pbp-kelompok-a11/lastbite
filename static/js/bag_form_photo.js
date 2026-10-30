// Pratinjau foto Surprise Bag yang dipilih
(() => {
  const input = document.getElementById('id_photo');
  const box = document.getElementById('sb-photo-preview-box');
  const img = document.getElementById('sb-photo-preview');
  if (!input || !box || !img) return;

  input.addEventListener('change', () => {
    const file = input.files && input.files[0];
    if (!file || !file.type.startsWith('image/')) return;
    img.src = URL.createObjectURL(file);
    box.hidden = false;
  });
})();