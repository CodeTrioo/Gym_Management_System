/* ─── cloudinary.js ─── */
/* Global Cloudinary upload helper + media input component */

async function uploadToCloudinary(file, cloudName, uploadPreset, resourceType, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("upload_preset", uploadPreset);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    // Use the specific resourceType endpoint (image, video, raw)
    xhr.open("POST", `https://api.cloudinary.com/v1_1/${cloudName}/${resourceType}/upload`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        const data = JSON.parse(xhr.responseText);
        resolve(data.secure_url);
      } else {
        const errorMsg = `Cloudinary error: ${xhr.status} ${xhr.responseText}`;
        console.error(errorMsg);
        reject(new Error(errorMsg));
      }
    };
    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send(formData);
  });
}

/**
 * Initialize a media input group.
 * Usage: initMediaInput({ containerId, urlFieldId, cloudName, uploadPreset, type:'image'|'video' })
 */
function initMediaInput({ containerId, urlFieldId, cloudName, uploadPreset, type = 'image' }) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = `
    <div class="media-tabs">
      <button type="button" class="media-tab active" data-tab="upload">⬆ Upload</button>
      <button type="button" class="media-tab" data-tab="url">🔗 Paste URL</button>
    </div>
    <div data-panel="upload">
      <div class="media-upload-area" id="${containerId}-drop">
        <p>📁 Click or drag ${type === 'video' ? 'a video file / paste link' : 'an image'} here</p>
        <input type="file" id="${containerId}-file" accept="${type === 'video' ? 'video/*' : 'image/*'}" style="display:none">
      </div>
      <div class="upload-progress" id="${containerId}-progress">
        <div class="upload-progress-bar" id="${containerId}-bar"></div>
      </div>
    </div>
    <div data-panel="url" style="display:none">
      <input type="url" class="form-control" id="${containerId}-url-input" placeholder="Paste ${type === 'video' ? 'YouTube or video' : 'image'} URL here">
    </div>
    <div id="${containerId}-preview"></div>
  `;

  const urlField = document.getElementById(urlFieldId);
  const fileInput = container.querySelector(`#${containerId}-file`);
  const dropArea = container.querySelector(`#${containerId}-drop`);
  const progressEl = container.querySelector(`#${containerId}-progress`);
  const progressBar = container.querySelector(`#${containerId}-bar`);
  const urlInput = container.querySelector(`#${containerId}-url-input`);
  const preview = container.querySelector(`#${containerId}-preview`);

  // Tab switching
  container.querySelectorAll('.media-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      container.querySelectorAll('.media-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const panel = tab.dataset.tab;
      container.querySelectorAll('[data-panel]').forEach(p => {
        p.style.display = p.dataset.panel === panel ? '' : 'none';
      });
    });
  });

  // File upload
  dropArea.addEventListener('click', () => fileInput.click());
  dropArea.addEventListener('dragover', e => { e.preventDefault(); dropArea.style.background = 'var(--teal-glow)'; });
  dropArea.addEventListener('dragleave', () => dropArea.style.background = '');
  dropArea.addEventListener('drop', e => {
    e.preventDefault();
    dropArea.style.background = '';
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });

  async function handleFile(file) {
    progressEl.style.display = 'block';
    progressBar.style.width = '0%';
    try {
      const url = await uploadToCloudinary(file, cloudName, uploadPreset, type, (pct) => {
        progressBar.style.width = pct + '%';
      });
      urlField.value = url;
      renderMediaPreview(url, type, preview);
      progressEl.style.display = 'none';
      showToast('✅ Uploaded successfully!', 'success');
    } catch (err) {
      progressEl.style.display = 'none';
      showToast('❌ Upload failed: ' + err.message, 'error');
    }
  }

  // URL input
  urlInput.addEventListener('input', () => {
    const val = urlInput.value.trim();
    urlField.value = val;
    if (val) renderMediaPreview(val, type, preview);
  });
}

/**
 * Render a preview for an image or video into a container element.
 */
function renderMediaPreview(url, type, container) {
  if (typeof container === 'string') container = document.getElementById(container);
  if (!container) return;
  if (!url) { container.innerHTML = ''; return; }

  if (type === 'video') {
    let embedUrl = url;
    let isYT = false;
    if (url.includes('youtube.com/watch?v=')) {
      embedUrl = 'https://www.youtube.com/embed/' + url.split('v=')[1].split('&')[0];
      isYT = true;
    } else if (url.includes('youtu.be/')) {
      embedUrl = 'https://www.youtube.com/embed/' + url.split('youtu.be/')[1].split('?')[0];
      isYT = true;
    }
    container.innerHTML = isYT
      ? `<iframe src="${embedUrl}" style="width:100%;max-width:360px;height:200px;border-radius:8px;margin-top:8px" frameborder="0" allowfullscreen></iframe>`
      : `<video src="${url}" controls style="max-width:100%;max-height:200px;border-radius:8px;margin-top:8px"></video>`;
  } else {
    container.innerHTML = `<img src="${url}" class="media-preview" onerror="this.style.display='none'">`;
  }
}
